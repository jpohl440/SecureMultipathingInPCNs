def get_pairs(n):
	nodes = [i for i in range(n)]
	node_pairs = []
	while len(nodes) > 1:
		n = nodes.pop(0)
		for m in nodes:
			node_pairs.append([n, m])
	
	print(f"Node pairs: {node_pairs}")
	print(f"number of node pairs: {len(node_pairs)}")
	
	'''
	This code takes a list with n nodes and creates a list including all real pairs of nodes (n*(n-1)/2 pairs). For small n this works fine. However, the LN consists of 15.000+ nodes, for which the list of pairs would get really long (100+ million pairs).
	
	Assuming each pair consists of two node IDs (= strings of 66 characters each), each pair should take 212 bytes of memory according to stack exchange (https://stackoverflow.com/questions/9445201/python-size-of-strings-in-memory). This results in a total memory required of more than 212*100000000 bytes = 21 GB just for storing the list of pairs. This is not feasible. Itertools to the rescue.
	'''




'''
### CLN SOURCE CODE TO BE REVERSE ENGINEERED ###

/*****************************************************************************
 * presplit -- Early MPP splitter modifier.
 *
 * This splitter modifier is applied to the root payment, and splits the
 * payment into parts that are more likely to succeed right away. The
 * parameters are derived from probing the network for channel capacities, and
 * may be adjusted in future.
 */


/*By probing the capacity from a well-connected vantage point in the network
 * we found that the 80th percentile of capacities is >= 9765 sats.
 *
 * Rounding to 10e6 msats per part there is a ~80% chance that the payment
 * will go through without requiring further splitting. The fuzzing is
 * symmetric and uniformy distributed around this value, so this should not
 * change the success rate much. For the remaining 20% of payments we might
 * require a split to make the parts succeed, so we try only a limited number
 * of times before we split adaptively.
 *
 * Notice that these numbers are based on a worst case assumption that
 * payments from any node to any other node are equally likely, which isn't
 * really the case, so this is likely a lower bound on the success rate.
 *
 * As the network evolves these numbers are also likely to change.
 *
 * Finally, if applied trivially this splitter may end up creating more splits
 * than the sum of all channels can support, i.e., each split results in an
 * HTLC, and each channel has an upper limit on the number of HTLCs it'll
 * allow us to add. If the initial split would result in more than 1/3rd of
 * the total available HTLCs we clamp the number of splits to 1/3rd. We don't
 * use 3/3rds in order to retain flexibility in the adaptive splitter.
 */
#define MPP_TARGET_SIZE (10 * 1000 * 1000)
#define PRESPLIT_MAX_HTLC_SHARE 3

/* How many parts do we split into before we increase the bucket size. This is
 * a tradeoff between the number of payments whose parts are identical and the
 * number of concurrent HTLCs. The larger this amount the more HTLCs we may
 * end up starting, but the more payments result in the same part sizes.*/
#define PRESPLIT_MAX_SPLITS 16

static u32 payment_max_htlcs(const struct payment *p)
{
	const struct payment *root;
	struct channel_hint *h;
	u32 res = 0;
	for (size_t i = 0; i < tal_count(p->channel_hints); i++) {
		h = &p->channel_hints[i];
		if (h->local && h->enabled)
			res += h->htlc_budget;
	}
	root = p;
	while (root->parent)
		root = root->parent;
	if (res > root->max_htlcs)
		res = root->max_htlcs;
	return res;
}



static void presplit_cb(struct presplit_mod_data *d, struct payment *p)
{
	struct payment *root = payment_root(p);

	if (p->step == PAYMENT_STEP_INITIALIZED) {
		# The presplitter only acts on the root and only in the first step.
		size_t count = 0;
		struct amount_msat target, amt = p->amount;
		
		/* Divide it up if we can, but it might be v low already */
		if (htlcs >= PRESPLIT_MAX_HTLC_SHARE)
			htlcs /= PRESPLIT_MAX_HTLC_SHARE;

		int targethtlcs =
		    p->amount.millisatoshis / target_amount; /* Raw: division */
		if (htlcs == 0) {
			p->abort = true;
			return payment_fail(
			    p, "Cannot attempt payment, we have no channel to "
			       "which we can add an HTLC");
		} else if (targethtlcs > htlcs) {
			paymod_log(p, LOG_INFORM,
				   "Number of pre-split HTLCs (%d) exceeds our "
				   "HTLC budget (%d), skipping pre-splitter",
				   targethtlcs, htlcs);
			return payment_continue(p);
		} else
			target = amount_msat(target_amount);

		/* If we are already below the target size don't split it
		 * either. */
		if (amount_msat_greater(target, p->amount))
			return payment_continue(p);

		payment_set_step(p, PAYMENT_STEP_SPLIT);
		/* Ok, we know we should split, so split here and then skip this
		 * payment and start the children instead. */
		while (!amount_msat_eq(amt, AMOUNT_MSAT(0))) {
			double multiplier;

			struct payment *c =
			    payment_new(p, NULL, p, p->modifiers);

			/* Annotate the subpayments with the bolt11 string,
			 * they'll be used when aggregating the payments
			 * again. */
			c->invstring = tal_strdup(c, p->invstring);

			/* Get ~ target, but don't exceed amt */
			c->amount = fuzzed_near(target, amt);

			if (!amount_msat_sub(&amt, amt, c->amount))
				paymod_err(
				    p,
				    "Cannot subtract %s from %s in splitter",
				    type_to_string(tmpctx, struct amount_msat,
						   &c->amount),
				    type_to_string(tmpctx, struct amount_msat,
						   &amt));

			/* Now adjust the constraints so we don't multiply them
			 * when splitting. */
			multiplier = amount_msat_ratio(c->amount, p->amount);
			if (!amount_msat_scale(&c->constraints.fee_budget,
					       c->constraints.fee_budget,
					       multiplier))
				abort(); /* multiplier < 1! */
			payment_start(c);
			/* Why the wordy "new partid n" that we repeat for
			 * each payment?
			 * So that you can search the logs for the
			 * creation of a partid by just "new partid n".
			 */
			if (count == 0)
				tal_append_fmt(&partids, "new partid %"PRIu32, c->partid);
			else
				tal_append_fmt(&partids, ", new partid %"PRIu32, c->partid);
			count++;
		}

		p->result = NULL;
		p->route = NULL;
		p->why = tal_fmt(
		    p,
		    "Split into %zu sub-payments due to initial size (%s > %s)",
		    count,
		    type_to_string(tmpctx, struct amount_msat, &root->amount),
		    type_to_string(tmpctx, struct amount_msat, &target));
		paymod_log(p, LOG_INFORM, "%s: %s", p->why, partids);
	}
	payment_continue(p);
}

REGISTER_PAYMENT_MODIFIER(presplit, struct presplit_mod_data *,
			  presplit_mod_data_init, presplit_cb);

### END OF TO-BE-REVERSE-ENGINEERED SECTION ###
'''




# reference for default MAX_CONCURRENT_HTLCS value:
# https://github.com/ElementsProject/lightning/blob/8c9fa457babd8ac09009fb93fe7a1a6409aba911/lightningd/options.c#L781-L835
MAX_CONCURRENT_HTLCS	= 30

# reference for majority of the following multipathing code:
# https://github.com/ElementsProject/lightning/blob/1da9b30b9abd26e9861ae199c2754f3d9cf7249f/plugins/libplugin-pay.c#L3384-L3788
MPP_TARGET_SIZE			= 10*1000*1000
PRESPLIT_MAX_SPLITS		= 16


def payment_supports_mpp(p):
	# ;-)
	return True


def presplit_cb(amount):
	# TODO: Should this be a separate function or if does it go in route_payment() and is executed when multipathing=True?
	if not payment_supports_mpp(amount):
		print("Multipathing not supported with this payment.")
		return -1
	
	'''
	We aim for at most PRESPLIT_MAX_SPLITS parts, even for large values. To achieve this we take the base amount and multiply it by the number of targetted parts until the total amount divided by part amount gives us at most that number of parts.
	'''
	target_amount = 10*1000*1000  # 10 million Millisatoshis = 10.000 Satoshis
	
	while (target_amount * PRESPLIT_MAX_SPLITS) < amount:
		target_amount *= PRESPLIT_MAX_SPLITS
	
	htlcs = payment_max_htlcs(p);  # TODO: htlcs = MAX_CONCURRENT_HTLCS?




def get_path_counter(n):
	return n[1]["path_counter"]


# This function takes a list of nodes and prints the cumulative percentage of paths that go through it
def print_cumulative_percentage_of_paths_going_through_top_n_nodes(nodes, top_n):
	number_of_paths = 0
	for i in range(top_n):
		number_of_paths += get_path_counter(nodes[i])
		perc = number_of_paths/total_number_of_paths
		print(f"{int(100*perc)}% of paths going through top {i+1} nodes")  # TODO: Find out how to make this into a nice plot 
	

def print_cumulative_percentage_of_paths(node):


def get_node_pairs(G):
	return [["0","1"], ["0","2"], ["1","2"]]  # TODO: return iterator over all pairs of nodes using itertools (?)
	

def increment_path_counter(path):
	# Disregard source nodes since source nodes do not perform payment griefing
	for n in path[1:]:
		G.nodes[n]["path_counter"]++  # TODO: Check if I can manipulate integer node attributes like this on a sample graph


def route_payment(src, tgt, amount, multipathing=False)
 	if not nx.has_path(G, src, tgt):
 		total_number_of_paths--
 		print(f"No path from {src} to {tgt}")
 	else:
		path = nx.shortest_path(G, src, tgt)
        increment_path_counter(path)
		nodes_by_path_counter = sorted(G.nodes(), key=lambda n: G.nodes[n]["path_counter"])  # TODO: Check if this works on a sample graph

		top_n = 10
		print_cumulative_percentage_of_paths_going_through_top_n_nodes(nodes_by_path_counter, top_n)



total_number_of_paths = int(n*(n-1)/2)

def all_pairs_transaction(amount):
	node_pairs = get_node_pairs()  # Use itertools for this. Storing 112 million pairs of strings takes 21+ GB of memory which is not feasible.
	for p in node_pairs:
	 	src, tgt = p[0], p[1]
 		route_payment(src, tgt, amount, multipathing=False)
 		
	

# Add to main():
betw_dict = nx.betweenness_centrality(G)
nx.set_node_attributes(G, values=betw_dict, name="betweenness")
nx.set_node_attributes(G, values=0, name="path_counter")  # TODO: Check if this is the same as betweenness on a sample graph
nx.set_edge_attributes(G, values=MAX_CONCURRENT_HTLCS, name="htlc_budget")
