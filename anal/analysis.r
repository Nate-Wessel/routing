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
summary(entropy_lm)

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
# can't use stat_ecdf because it doesn't take weights
sample_pairs = ods %>% select(pair,weight) %>% distinct() %>% sample_n(size=25,weight=weight) %>% select(pair)
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-ecdf.pdf',width=8,height=3)
	times %>% 
		inner_join(sample_pairs) %>% # this is a filter
		gather(d_hab,d_real,key='Strategy',value='delta') %>% 
		filter( delta >= 0 ) %>% # ie is not null
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

# find 90th percentile time delta per (od,period) for real and habit
ods2 = times %>% 
	group_by(pair,period) %>% 
	filter(any,hab,real) %>%
	summarise( 
		mean_any = mean(any),
		dm_hab90 = quantile(d_hab,.9), # momentary
		dm_real90 = quantile(d_real,.9) # momentary
	) %>% 
	inner_join(ods)

# density plot of 90th percentile delta-T
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-T-KDE.pdf',width=5,height=2)
	ods2 %>% 
		gather(dm_hab90,dm_real90,key='strategy',value='d_90') %>%
		ggplot(data=.) + 
			geom_density(aes(d_90,weight=weight,fill=strategy),alpha=.3,color=NA) + 
			coord_trans(limx=c(0,35)) + theme_light() + 
			labs(x='90th percentile travel time risk')
dev.off()
	
#what predicts momentary time deltas?
full_model = lm( dm_hab90 ~ grid + retro_ent + retro_it_n + from_grid + period, data=ods2, weights=weight)
summary(full_model)

terse_model = lm( dm_hab90 ~ retro_ent, data=ods2, weights=weight)
summary(terse_model)

# density plot of global travel time distributions
library('spatstat')
cairo_pdf('~/Dropbox/diss/routing/paper/figures/global-tt-dists.pdf',width=5,height=2)
	times %>%
		filter(any,real,hab) %>%
		gather(any,real,hab,key='strategy',value='tt') %>%
		#group_by(strategy) %>%
		#summarise( weighted.quantile(tt,w=weight,probs=.9) )
			ggplot(data=.) + 
			geom_density(aes(tt,weight=weight,fill=strategy,color=strategy),alpha=.3) + 
			coord_trans(limx=c(0,120)) + 
			theme_light() + 
			labs(x='Global travel time distributions (minutes)')
dev.off()

# plot a distribution of 90th percentile distribution differences
cairo_pdf('~/Dropbox/diss/routing/paper/figures/per-pair-90th-diffs.pdf',width=5,height=2)
	times %>% 
		select(pair,period,weight,any,hab,real) %>% 
		filter(any,hab,real) %>%
		gather(real,hab,key='strategy',value='tt') %>% 
		group_by(strategy,pair,period) %>% 
		summarise( d_tt90 = quantile(tt,.9) - quantile(any,.9) ) %>% 
		inner_join(ods[,c('pair','period','weight')]) %>%
		group_by(strategy) %>% 
		summarise(weighted.median(d_tt90,w=weight))
		ggplot(data=.) + 
			geom_density(aes(d_tt90,weight=weight,color=strategy,fill=strategy),alpha=.3) +
			coord_trans(limx=c(0,20)) + 
			theme_light() 
dev.off()

# calculate median differences at percentiles and slopes of relation with S
ods2 = times %>% 
	filter(any,hab,real) %>%
	group_by(pair,period) %>% 
	summarise( 
		mean_any = mean(any),
		hab90 = quantile(hab,.9) - quantile(any,.9), # distribution
		real90 = quantile(real,.9) - quantile(any,.9)# distribution
	) %>% 
	inner_join(ods) %>% 
	ggplot(data=.) + 
		geom_point(aes(retro_ent,hab90,alpha=weight)) + 
		coord_trans(limy=c(0,30))

# what predicts 90th percentile distribution differences?
full_model = lm( hab90 ~ grid + from_grid + period + mean_any, data=ods2, weights=weight)
summary(full_model)

terse_model = lm( hab90 ~ retro_ent, data=ods2, weights=weight)
print(summary(terse_model))

# ...in progress...
ods2 %>% 
	gather(dt_hab90,dt_real90,key='strategy',value='dt90') %>% 
	mutate(dist_bin = cut(grid,breaks=seq(0,50,by=10))) %>% 
	ggplot(data=.) + 
	geom_point(mapping=aes(retro_ent,dt90,alpha=weight,color=strategy)) + 
	theme_light() + 
	facet_wrap(~period) + 
	coord_trans(limy=c(0,15)) 
