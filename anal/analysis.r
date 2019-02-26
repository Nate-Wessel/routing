#######################################
# read in OD level data and assign weights to observations
#######################################
# read in the OD pairs
ods = read.csv('~/routing/data/untracked/am-peak-od-stats.csv')
# name the data, remove unecessary fluff
rownames(ods) = paste0(ods$o,'->',ods$d)
ods$pair = factor(rownames(ods))
ods$o = ods$d = ods$i = NULL
# assign weights based on areas
ods$weight = ods$o_area * ods$d_area
ods$weight = ods$weight / sum(ods$weight)
# and weights based on length distributions
sample_density = density( ods$grid, weights=ods$weight, from=0, to=47, n=516, bw=1 )
obs = read.csv('~/routing/data/TTS/observed_trip_lengths.csv')
observed_density = density( obs$grid_dist, weights=obs$trips/sum(obs$trips), from=0, to=47, n=516, bw=1 )
cairo_pdf('~/Dropbox/diss/routing/paper/figures/weights-adjustment.pdf',width=6,height=3)
	par(mar=c(4,0,2,0),family='serif')
	plot(observed_density,main='Unweighted Sample vs. Observed Trip Lengths',
		  col='red',xlab='Kilometers (Manhattan Distance)',
		  bty='n',yaxt='n',ylab='')
	lines(sample_density,col='grey',lty=2)
	# adjust weights iteratively to mimic desired distribution
	for(i in 1:15){
		adj_factor = observed_density$y / sample_density$y
		ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$grid)$y
		ods$weight = ods$weight / sum(ods$weight)
		sample_density = density( ods$grid, weights=ods$weight, from=0, to=47, n=516, bw=1 )
		lines(sample_density,col=rgb(0,0,1,alpha=0.1))
	}
dev.off()
remove(i,adj_factor,observed_density,sample_density,obs)

###############################################
# read in the db-estimated departure times data
###############################################
t = read.csv( '~/routing/data/untracked/am-peak-times.csv', colClasses=c('hour'='factor') )
t$pair = factor(paste0(t$o,'->',t$d))
t$o = t$d = NULL
# add weights by OD
t = merge( x=t, y=ods[,c('pair','weight')], all.x=T, by='pair' )
# add time deltas
t$delta_hab = t$hab/t$any 
t$delta_real = t$real/t$any
# how often are the alternatives simply equivalent?
sum((t$any==t$hab)*t$weight,na.rm=T)/sum(t$weight)
sum((t$any==t$real)*t$weight,na.rm=T)/sum(t$weight)
# 
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
	wtd.hist( ods$sched_it_n, weight=ods$weight, breaks, border=F, col=rgb(1,0,0,alpha=.50),
		main='Itinerary Counts', xlab='Count', ylab='Weighted Frequency' )
	wtd.hist( ods$retro_it_n, weight=ods$weight, breaks, border=F, col=rgb(0,0,1,alpha=.25), add=T )
	remove(breaks)
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
