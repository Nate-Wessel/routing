# read in the OD pairs
ods = read.csv('~/routing/data/static_summary.csv')
# assign weights based on areas
ods$weight = ods$o_area * ods$d_area
ods$weight = ods$weight / sum(ods$weight)
# and weights based on length distributions
sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
temp =  c(5,7,10,15,20,25)
tempw = c(1,2,1 ,1 ,1 ,.5)
observed_density = density( temp, weights=tempw/sum(tempw), from=0, to=45, n=516, bw=4 )
plot(sample_density,ylim=c(0,0.06))
lines(observed_density,col='red',lty=2)
# adjust weights iteratively to mimic desired distribution
for(i in 1:20){
	adj_factor = observed_density$y / sample_density$y
	ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$arc)$y
	ods$weight = ods$weight / sum(ods$weight)
	sample_density = density( ods$arc, weights=ods$weight, from=0, to=45, n=516, bw=1 )
	lines(sample_density,col=rgb(0,0,1,alpha=0.2))
}

#d = read.csv('~/routing/data/all_times.csv')
#d$o = factor(d$o)
#d$d = factor(d$d)
#d$hour = factor(d$hour)