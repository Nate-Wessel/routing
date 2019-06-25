######################
##### READ DATA ######
######################
# read in OD level data (weighted)
source('~/routing/anal/read-ods.r')
# read in estimated trip times, weighted by OD pair
source('~/routing/anal/read-times.r')

#####################################
# analysis will proceed as the paper
#####################################

# itinerary frequency histogram
cairo_pdf('~/Dropbox/diss/the/figures/3/itinerary-count-hist.pdf',width=5,height=3)
	ggplot(ods) +
		geom_bar(mapping=aes(x=it_n)) +
		facet_wrap(~period) + 
		theme_minimal( ) + theme(panel.spacing.x = unit(4, "mm")) + 
		coord_trans(limx=c(0,25)) +
		labs(x='Number of Itineraries',y='Frequency')
dev.off()

# how many itineraries does a typical trip have?
ods %>%
	summarise( 
		median  = median(it_n),
		`90pct` = quantile(it_n,probs=.9)
	)

# Plot entropy ECDF
cairo_pdf('~/Dropbox/diss/the/figures/3/entropy-ecdf.pdf',width=5,height=3)
	ggplot(ods) + 
		stat_ecdf( aes(x=entropy,color=period) ) + 
		coord_flip(xlim=c(0,4)) + 
		labs(y='Cumulative Probability',x='Entropy (bits)') + 
		theme_light()
dev.off()

# correlation of entropy between time periods 
ods %>% 
	select(pair,period,entropy) %>%
	spread(period,entropy) %>%
	select(-pair) %>%
	cor(.)

# spatial and other predictors of entropy
summary(lm( entropy ~ grid_dist + from_grid + crosses_sub + real_flow, data=ods))

# density plot of global travel time distributions
cairo_pdf('~/Dropbox/diss/the/figures/3/global-tt-dists.pdf',width=7,height=4)
	times %>%
		# filter for observations with non-null values
		filter(any,real,hab) %>%
		select(any,real,hab,period) %>%
		rename(Optimal=any,Habit=hab,Realtime=real) %>%
		gather(Optimal,Realtime,Habit,key='Strategy',value='tt') %>%
		#group_by(period) %>%
		#summarise( quantile(tt,probs=.5) )
		ggplot(data=.) + 
			geom_density(aes(tt,fill=Strategy,color=Strategy),alpha=.3,bw=1) + 
			coord_trans(limx=c(0,120)) + 
			facet_wrap(~period) +
			labs(x='Global travel time distributions (minutes)') +
			theme_minimal() + theme(panel.spacing.x = unit(4, "mm"))
dev.off()

# Basic descriptive statistics of the above distributions
times %>% 
	select(pair,period,any,hab,real) %>% 
	filter(any,hab,real) %>%
	gather(any,real,hab,key='Strategy',value='tt') %>%
	group_by(period,Strategy) %>%
	summarise(
		mean = mean(tt),
		pct50 = quantile(tt,.5),
		pct90 = quantile(tt,.9)
	)

# density plot of change in median travel times
cairo_pdf('~/Dropbox/diss/the/figures/3/median-pair-diffs.pdf',width=6,height=3)
	times %>% 
		filter(any,hab,real) %>%
		group_by(pair,period) %>% 
		summarise( # absolute change in relative 90th pctl travel times
			Habit    = quantile(hab,.5) - quantile(any,.5),
			Realtime = quantile(real,.5) - quantile(any,.5)
		) %>% 
		#ungroup() %>%
		#summarize(median(Habit),median(Realtime))
		gather(Habit,Realtime,key='Strategy',value='d_90') %>%
		ggplot(data=.) + 
			geom_density(aes(d_90,fill=Strategy),alpha=.3,color=NA,bw=.5) + 
			coord_trans(limx=c(0,12)) + 
			labs(x='Shift in Median Travel Time per OD (minutes)',y='Density') + 
			facet_wrap(~period) + 
			theme_minimal() + theme(panel.spacing.x = unit(4, "mm"))
dev.off()

# what is associated with greater X?
reg_data = times %>% 
	filter(any,hab,real) %>%
	group_by(pair,period) %>% 
	summarise( # absolute change in relative 90th pctl travel times
		med_any  = median(any),
		habit_md = median(hab) - median(any),
		real_md  = median(real) - median(any)
	) %>%
	inner_join(ods) %>%
	mutate(max_from_sub=max(o_km_from_sub,d_km_from_sub))
summary( lm( 
	real_md ~ grid_dist + from_grid + crosses_sub + real_flow + max_from_sub, 
	data=reg_data
) )
remove(reg_data)

# how often are the alternatives simply equivalent?
times %>% summarise(
	hab_percent_optimal  = sum((any==hab),na.rm=T)/sum(!is.na(any*hab)),
	real_percent_optimal = sum((any==real),na.rm=T)/sum(!is.na(any*hab))
)

# plot sampled ECDF travel time deltas
# can't use stat_ecdf because it doesn't take weights
sample_pairs = ods %>% sample_n(size=100) %>% select(pair)
cairo_pdf('~/Dropbox/diss/the/figures/3/delta-ecdf.pdf',width=8,height=4)
	times %>% 
	#	filter(period=='evening') %>%
		inner_join(sample_pairs) %>% # this is a filter
		rename(`Habitual Strategy`=d_hab,`Real-time Strategy`=d_real) %>% 
		gather(ends_with('Strategy'),key='Strategy',value='delta') %>% 
		filter( delta >= 0 ) %>% # ie is not null
		ggplot(data=.) + 
			geom_hline(aes(yintercept=.9),color='red') + 
			stat_ecdf( aes(x=delta,group=pair), color='black', alpha=0.15 ) + 
			theme_minimal() +
			coord_flip(xlim=c(0,25)) +
			labs(y='Cumulative Probability per OD',x='Travel Time Difference (minutes)') + 
			facet_wrap(~Strategy)
dev.off()
remove(sample_pairs)





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


	
#what predicts momentary time deltas?
summary(lm( dm_hab90 ~ grid_dist + entropy + it_n + from_grid + period, data=ods2))
summary(lm( dm_hab90 ~ entropy, data=ods2))

# plot a distribution of 90th percentile distribution differences
cairo_pdf('~/Dropbox/diss/the/figures/3/per-pair-90th-diffs.pdf',width=5,height=2)
	times %>% 
		select(pair,period,any,hab,real) %>% 
		filter(any,hab,real) %>%
		gather(real,hab,key='Strategy',value='tt') %>% 
		group_by(Strategy,pair,period) %>% 
		summarise( d_tt90 = quantile(tt,.9) - quantile(any,.9) ) %>% 
		inner_join(ods) %>%
		#group_by(Strategy) %>% 
		#summarise(weighted.median(d_tt90,w=weight)) %>% 
		ggplot(data=.) + 
			geom_density(aes(d_tt90,color=Strategy,fill=Strategy),alpha=.3) +
			coord_trans(limx=c(0,25)) + 
			labs(x='Shift in 90th Percentile Travel Time (Minutes)') +
			theme_minimal()
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
		geom_point(aes(entropy,hab90,alpha=weight)) + 
		coord_trans(limy=c(0,30))

# what predicts 90th percentile distribution differences?
summary(lm( 
	real90 ~ grid_dist + from_grid + pmax(o_km_from_sub,d_km_from_sub) + real_flow + crosses_sub + sqrt(o_area) + sqrt(d_area), 
	data=ods2
))

summary(lm( dm_real90 ~ entropy, data=ods2))

