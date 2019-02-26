# read in OD level data (weighted)
source('~/routing/anal/read-and-weight-ods.r')

# read in estimated trip times, weighted by OD pair
source('~/routing/anal/read-times.r')




# how often are the alternatives simply equivalent?
sum((times$any==times$hab)*times$weight,na.rm=T)/sum(times$weight)
sum((times$any==times$real)*times$weight,na.rm=T)/sum(times$weight)

################################
# analyze stats per OD
################################
# aggregate some time stats to the OD level
# this seems to keep things in the right order
ods[levels(ods$pair),'mean_any_time'] = by(t$any,t$pair,mean,na.rm=T)
ods[levels(ods$pair),'mean_delta_hab'] = by(t$delta_hab,t$pair,mean,na.rm=T)
ods[levels(ods$pair),'mean_delta_real'] = by(t$delta_real,t$pair,mean,na.rm=T)
#ods[order(-ods$mean_delta_hab),]
head(t[order(-t$delta_hab),])
head(ods[order(-ods$mean_delta_hab),])

# compare entropy to azimuth and distance
# first determine angle away from street grid
ods$from_grid = apply(cbind(-ods$azimuth%%73,ods$azimuth%%73),1,min)
lmr = lm( retro_it_n ~ grid + from_grid, data=ods, weights=weight)
print(summary(lmr))
# there is no relation with azimuth

# do some (weighted) descriptive stats of the itineraries generated
library('weights')
cairo_pdf('~/Dropbox/diss/routing/paper/figures/itinerary-count-hist.pdf',width=5,height=4)
	breaks = seq(-0.5,10.5,1)
	col1 = rgb(1,0,0,alpha=.50)
	col2 = rgb(0,0,1,alpha=.25)
	wtd.hist( ods$sched_it_n, weight=ods$weight, breaks, border=F, col=col1,
		main='Itinerary Counts', xlab='Count', ylab='Weighted Frequency' )
	wtd.hist( ods$retro_it_n, weight=ods$weight, breaks, border=F, col=col2, add=T )
	legend(x=6,y=.25,legend=c('sched','retro'),fill=c(col1,col2),border=rgb(1,1,1,alpha=1))
	remove(breaks,col1,col2)
dev.off()



###################################
#
###################################
# plot distributions of time deltas
cairo_pdf('~/Dropbox/diss/routing/paper/figures/delta-t.pdf',width=6,height=4)
	# calculate diff densities
	i = !is.na(t$delta_hab) & t$delta_hab > 0
	sum(i)
	delta_hab = density(
		x=t[i,'delta_hab'], weights=t[i,'weight'] / sum(t[i,'weight']),
		bw=.5, from=0, to=40, n=516
	)
	i = !is.na(t$delta_real) & t$delta_real > 0
	delta_real = density(
		x=t[i,'delta_real'], weights=t[i,'weight'] / sum(t[i,'weight']),
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
