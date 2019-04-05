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
	ggplot(ods) +
		geom_bar(mapping=aes(x=it_n,weight=weight)) +
		facet_wrap(~period) + 
		theme_light() +
		coord_trans(limx=c(0,25)) +
		labs(x='Itineraries',y='Frequency')
dev.off()

# what predicts entropy?
entropy_lm = lm( 
	entropy ~ grid_dist + from_grid + crosses_sub + real_flow + o_km_from_sub * d_km_from_sub, 
	data=ods, 
	weights=weight
)
summary(entropy_lm)

# Plot entropy ECDF
cairo_pdf('~/Dropbox/diss/routing/paper/figures/entropy-ecdf.pdf',width=5,height=3)
	ods %>%
	arrange(entropy) %>% 
	group_by(period) %>% 
	mutate( cum_w = cumsum(weight) / sum(weight) ) %>%
	ggplot(data=.) + 
		geom_line( aes(x=cum_w,y=entropy,color=period) ) + 
		coord_trans(limy=c(0,4)) + 
		labs(x='Cumulative Probability',y='Entropy (bits)') + 
		theme_light()
dev.off()

# how often are the alternatives simply equivalent?
times %>% summarise(
	hab_percent_optimal  = sum((any==hab )*weight,na.rm=T)/sum(weight),
	real_percent_optimal = sum((any==real)*weight,na.rm=T)/sum(weight)
)

times %>% 
	group_by(pair) %>% 
	summarize( 
		optimal_pct = sum(any==real,na.rm=T)/sum(!is.na(real)),
		weight = mean(weight)
	) %>%
	arrange(-optimal_pct) %>% 
	mutate( cump = cumsum(weight) / sum(weight) ) %>% 
	ggplot(data=.) + 
		geom_line(aes(cump,optimal_pct))

# plot sampled ECDF travel time deltas
# can't use stat_ecdf because it doesn't take weights
sample_pairs = ods %>% sample_n(size=100,weight=weight) %>% select(pair)
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-ecdf.pdf',width=8,height=4)
	times %>% 
		inner_join(sample_pairs) %>% # this is a filter
		rename(habit=d_hab,realtime=d_real) %>% 
		gather(habit,realtime,key='Strategy',value='delta') %>% 
		filter( delta >= 0 ) %>% # ie is not null
		group_by(pair,Strategy) %>%
		mutate( rank = row_number(delta) / max(row_number(delta))) %>%
		ggplot(data=.,aes(group=pair)) + 
			geom_vline(aes(xintercept=.9),color='red') + 
			geom_line( mapping=aes( rank, delta ), color='black',alpha=0.15 ) + 
			scale_alpha(range=c(.05,.6)) + 
			coord_trans(limy=c(0,25)) + 
			theme_minimal() + 
			facet_wrap(~Strategy) + 
			labs(x='Cumulative Probability',y='Travel Time Difference (minutes)')
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
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-T-KDE.pdf',width=6,height=3)
	ods2 %>% 
		rename( habit=dm_hab90, realtime=dm_real90 ) %>% 
		gather(habit,realtime,key='Strategy',value='d_90') %>%
		group_by(Strategy,period) %>% 
		mutate(weight = weight/sum(weight)) %>%
		ggplot(data=.) + 
			geom_density(aes(d_90,weight=weight,fill=Strategy),alpha=.3,color=NA) + 
			coord_trans(limx=c(0,35)) + theme_light() + 
			labs(x='90th Percentile Travel Time Risk',y='Density') + 
			facet_wrap(~period) + 
			theme_minimal()
dev.off()
	
#what predicts momentary time deltas?
full_model = lm( dm_hab90 ~ grid_dist + entropy + it_n + from_grid + period, data=ods2, weights=weight)
summary(full_model)

terse_model = lm( dm_real90 ~ entropy, data=ods2, weights=weight)
summary(terse_model)

# density plot of global travel time distributions
#library('spatstat')
cairo_pdf('~/Dropbox/diss/routing/paper/figures/global-tt-dists.pdf',width=5,height=2)
	times %>%
		# filter for observations with non-null values
		filter(any,real,hab) %>%
		select(any,real,hab,weight,period) %>%
		rename(Optimal=any,Habit=hab,Realtime=real) %>%
		gather(Optimal,Realtime,Habit,key='Strategy',value='tt') %>%
		group_by(Strategy,period) %>%
		mutate(weight = weight/sum(weight)) %>%
		#group_by(strategy) %>%
		#summarise( weighted.quantile(tt,w=weight,probs=.9) )
			ggplot(data=.) + 
			geom_density(aes(tt,weight=weight,fill=Strategy,color=Strategy),alpha=.3,bw=1) + 
			coord_trans(limx=c(0,120)) + 
			theme_minimal() + 
			facet_wrap(~period) +
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
