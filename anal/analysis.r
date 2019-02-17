#######################################
# read in OD level data and assign weights to observations
#######################################
# read in the OD pairs
ods = read.csv('~/routing/data/untracked/static_summary.csv')
# assign weights based on areas
ods$weight = ods$o_area * ods$d_area
ods$weight = ods$weight / sum(ods$weight)
# and weights based on length distributions

sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
obs = read.csv('~/routing/data/TTS/observed_trip_lengths.csv')
observed_density = density( obs$km, weights=obs$trips/sum(obs$trips), from=0, to=45, n=516, bw=1 )
plot(observed_density,main='Distribution Comparison',col='red')
lines(sample_density,col='grey',lty=2)
# adjust weights iteratively to mimic desired distribution
for(i in 1:10){
	adj_factor = observed_density$y / sample_density$y
	ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$arc)$y
	ods$weight = ods$weight / sum(ods$weight)
	sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
	lines(sample_density,col=rgb(0,0,1,alpha=0.1))
}
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
wtd.hist( ods$sched_it_n, weight=ods$weight, col=rgb(1,0,0,alpha=.50), border=F )
wtd.hist( ods$retro_it_n, weight=ods$weight, col=rgb(0,0,1,alpha=.25), border=F, add=T )
#d = read.csv('~/routing/data/all_times.csv')
#d$o = factor(d$o)
#d$d = factor(d$d)
#d$hour = factor(d$hour)