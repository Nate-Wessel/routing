# read in the OD pairs
ods = read.csv('~/routing/data/static_summary.csv')
# assign weights based on areas
ods$weight = ods$o_area * ods$d_area
ods$weight = ods$weight / sum(ods$weight)
# and weights based on length distributions

sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
obs = read.csv('~/routing/data/observed-trip-lengths.csv')
observed_density = density( obs$km, weights=obs$trips/sum(obs$trips), from=0, to=45, n=516, bw=1 )
plot(observed_density,col='red')
lines(sample_density,col='grey',lty=2)
# adjust weights iteratively to mimic desired distribution
for(i in 1:10){
	adj_factor = observed_density$y / sample_density$y
	ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$arc)$y
	ods$weight = ods$weight / sum(ods$weight)
	sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
	lines(sample_density,col=rgb(0,0,1,alpha=0.1))
}

#d = read.csv('~/routing/data/all_times.csv')
#d$o = factor(d$o)
#d$d = factor(d$d)
#d$hour = factor(d$hour)