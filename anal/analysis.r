######################
##### READ DATA ######
######################
# read in OD level data (weighted)
source('~/routing/anal/read-and-weight-ods.r')
# read in estimated trip times, weighted by OD pair
source('~/routing/anal/read-times.r')

#####################################
# analysis will proceed as the paper
#####################################

# itinerary frequency histogram
cairo_pdf('~/Dropbox/diss/routing/paper/figures/itinerary-count-hist.pdf',width=5,height=3)
	ods %>% 
	rename(retro=retro_it_n,sched=sched_it_n) %>% 
	gather(retro,sched,key='dataset',value='n') %>% 
	ggplot(data=.) +
		geom_bar(mapping=aes(x=n,weight=weight,fill=dataset),alpha=.50,position='identity') +
		facet_wrap(~period) + 
		theme_light()
dev.off()

# what predicts entropy?
entropy_lm = lm( sqrt(retro_ent) ~ grid + from_grid, data=ods, weights=weight)
print(summary(entropy_lm))

# Plot entropy ECDF
cairo_pdf('~/Dropbox/diss/routing/paper/figures/entropy-ecdf.pdf',width=5,height=3)
	ods %>%
	arrange(retro_ent) %>%
	mutate( retro_cum_w = cumsum(weight) / sum(weight) ) %>%
	arrange(sched_ent) %>%
	mutate( sched_cum_w = cumsum(weight) / sum(weight) ) %>%
	ggplot(data=.) + 
		geom_line( aes(x=retro_cum_w,y=retro_ent),color='red' ) + 
		geom_line( aes(x=sched_cum_w,y=sched_ent),color='blue' ) + 
		coord_trans(limy=c(0,4)) + 
		labs(x='Cumulative Probability',y='Shannon Entropy (bits)') + 
		theme_light()
dev.off()

# how often are the alternatives simply equivalent?
times %>% summarise(
	hab_percent_optimal  = sum((any==hab )*weight,na.rm=T)/sum(weight),
	real_percent_optimal = sum((any==real)*weight,na.rm=T)/sum(weight)
)


# plot sampled ECDF travel time deltas
sample_pairs = ods %>% select(pair,weight) %>% distinct() %>% sample_n(100,weight=weight) %>% select(pair)
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-ecdf.pdf',width=8,height=3)
	times %>% 
		inner_join(sample_pairs) %>% # this is a filter
		gather(d_hab,d_real,key='Strategy',value='delta') %>% 
		filter( delta >= 0 ) %>% 
		group_by(pair,Strategy) %>%
		mutate( rank = row_number(delta) / max(row_number(delta))) %>%
		ggplot(data=.,aes(group=pair,alpha=weight)) +
			geom_line( mapping=aes( rank, delta ), color='blue' ) +
			scale_alpha(range=c(.05,.6)) +
			geom_vline(aes(xintercept=.9),color='red') + 
			coord_trans(limy=c(0,25)) + 
			theme_minimal() +
			facet_wrap(~Strategy) +
			labs(x='Cumulative Probability',y='Habit Delta T (minutes)')
dev.off()
remove(sample_pairs)

# find 90th percentile time delta per (od,period) for real and habit
ods = times %>% 
	group_by(pair,period) %>% 
	summarise( 
		d_hab_90 = quantile(x=d_hab,probs=.9,na.rm=T),
		d_real_90 = quantile(x=d_real,probs=.9,na.rm=T)
	) %>% 
	inner_join(ods)
	 

#what predicts big time deltas?
full_model = lm( d_hab90 ~ grid + retro_ent + retro_it_n + from_grid + period, data=ods, weights=weight)
print(summary(full_model))

terse_model = lm( d_real90 ~ retro_ent, data=ods, weights=weight)
print(summary(terse_model))

