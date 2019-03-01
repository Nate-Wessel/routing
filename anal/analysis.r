######################
##### READ DATA ######
######################
# read in OD level data (weighted)
source('~/routing/anal/read-and-weight-ods.r')
# read in estimated trip times, weighted by OD pair
source('~/routing/anal/read-times.r')


#####################################
# very basic summary stats
#####################################
# itinerary frequency histogram
cairo_pdf('~/Dropbox/diss/routing/paper/figures/itinerary-count-hist.pdf',width=5,height=4)
	ggplot(data=ods) +
		geom_bar(
			mapping=aes(x=retro_it_n,weight=weight,fill=factor(sched_it_n)),
			alpha=.50,
			position='identity'
		) +
		facet_wrap(~period) + 
		theme_light()
dev.off()

# how often are the alternatives simply equivalent?
times %>% summarise(
	hab_percent_optimal  = sum((any==hab )*weight,na.rm=T)/sum(weight),
	real_percent_optimal = sum((any==real)*weight,na.rm=T)/sum(weight)
)


###################################################
##### get aggregate stats from times back to ods ##
###################################################
## time deltas
times %>% mutate(
	d_hab = hab - any,
	d_real = real - any
)

# find 90th percentile time delta per (od,period) for real and habit
summary_table = times %>% group_by(pair,period) %>% 
	summarise( 
		d_hab90 =  quantile(x=d_hab, probs=.9,na.rm=T),
		d_real90 = quantile(x=d_real,probs=.9,na.rm=T)
	)
ods = inner_join(ods,summary_table)
remove(summary_table)

# first determine angle away from street grid
ods$from_grid = apply(cbind(-ods$azimuth%%73,ods$azimuth%%73),1,min)

#what predicts big time deltas?
lmr = lm( d_hab90 ~ grid + from_grid + retro_ent, data=ods, weights=weight)
print(summary(lmr))
# there is no relation with azimuth





###################################
# plot distributions of time deltas
###################################
pcts = seq(0,.99,by=.01)
pct_vals = wtd.quantile(x=times$d_hab,q=pcts,na.rm=T,weight=times$weight)
plot(x=pcts*100,y=pct_vals,type='l',col='red')
grid()





cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-t.pdf',width=6,height=4)
	# calculate diff densities
	i = !is.na(t$delta_hab) & t$delta_hab > 0
	delta_hab = density( x=t[i,'delta_hab'], 
		weights=t[i,'weight'] / sum(t[i,'weight']),
		bw=.5, from=0, to=40, n=516
	)
	i = !is.na(t$delta_real) & t$delta_real > 0
	delta_real = density( x=t[i,'delta_real'], 
		weights=t[i,'weight'] / sum(t[i,'weight']),
		bw=.5, from=0, to=40, n=516 
	)
	# plot
	plot( 
		delta_real, ylim=c(0,.12),
		col='black', main='Travel time diffs', xlab='Minutes' )
	lines( delta_hab, col='red' )
dev.off()
remove(i)
gc()
