#######################################
# read in OD level data and assign weights to observations
#######################################
# read in the OD pairs
ods = read.csv('~/routing/data/untracked/summary.csv')
# assign weights based on areas
ods$weight = ods$o_area * ods$d_area
ods$weight = ods$weight / sum(ods$weight)
# and weights based on length distributions
sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
obs = read.csv('~/routing/data/TTS/observed_trip_lengths.csv')
observed_density = density( obs$km, weights=obs$trips/sum(obs$trips), from=0, to=45, n=516, bw=1 )
cairo_pdf('~/Dropbox/diss/routing/paper/figures/weights-adjustment.pdf',width=6,height=4)
	plot(observed_density,main='Distribution Comparison',col='red',xlab='Euclidean KM')
	lines(sample_density,col='grey',lty=2)
	# adjust weights iteratively to mimic desired distribution
	for(i in 1:15){
		adj_factor = observed_density$y / sample_density$y
		ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$arc)$y
		ods$weight = ods$weight / sum(ods$weight)
		sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
		lines(sample_density,col=rgb(0,0,1,alpha=0.1))
	}
dev.off()
remove(i,adj_factor,observed_density,sample_density)

################################
# analyse itinerary counts
################################
# compare entropy to azimuth and distance
# first determine angle away from street grid
ods$from_grid = apply(cbind(-ods$azimuth%%73,ods$azimuth%%73),1,min)
lmr = lm( ods$retro_ent ~ ods$arc + ods$from_grid, weights=ods$weight)
print(summary(lmr))
# there is no relation with azimuth

# do some (weighted) descriptive stats of the itineraries generated
library('weights')
cairo_pdf('~/Dropbox/diss/routing/paper/figures/itinerary-count-hist.pdf',width=4,height=3)
	wtd.hist( ods$sched_it_n, weight=ods$weight, col=rgb(1,0,0,alpha=.50), border=F )
	wtd.hist( ods$retro_it_n, weight=ods$weight, col=rgb(0,0,1,alpha=.25), border=F, add=T )
dev.off()
###############################################
# read in the db-estimated departure times data
###############################################
t = read.csv(
	'~/routing/data/untracked/all_times.csv',
	colClasses=c('o'='factor','d'='factor','hour'='factor')
)
# verify times are plausible
sum(t$any>t$hab,na.rm=T) / nrow(t)
sum(t$any>t$real,na.rm=T) / nrow(t)

# add weights by OD
t = merge( x=t, y=ods[,c('o','d','weight')], all.x=T, by=c('o','d') )

# how often are the alternatives simply equivalent?
sum((t$any==t$hab)*t$weight,na.rm=T)/sum(t$weight)
sum((t$any==t$real)*t$weight,na.rm=T)/sum(t$weight)

# plot a simple comparison of distributions of travel times
cairo_pdf('~/Dropbox/diss/routing/paper/figures/global-time-dists.pdf',width=6,height=4)
	i = !is.na(t$any)
	plot( 
		density(
			x=t[i,'any'], 
			weights=t[i,'weight'] / sum(t[i,'weight']),
			from=0, to=120, n=516
		),
		col='black',main='Travel time densities',xlab='Minutes'
	)
	i = !is.na(t$hab)
	lines( density(
		x=t[i,'hab'], 
		weights=t[i,'weight'] / sum(t[i,'weight']),
		from=0, to=120, n=516
	), col='red' )
	i = !is.na(t$real)
	lines( density(
		x=t[i,'real'], 
		weights=t[i,'weight'] / sum(t[i,'weight']),
		from=0, to=120, n=516
	), col='blue' )
dev.off()
remove(i)
gc()
