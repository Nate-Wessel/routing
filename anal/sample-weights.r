# apply sampling weights to all OD pairs based on O/D area and distance
library(tidyverse)
# all possible od pairs
ods = read_csv('~/routing/data/sampled-ODs/all.csv')
ods$weight = ods$o_area * ods$d_area
sample_density = density( ods$grid_dist, from=0, to=47, n=516, bw=1 )

obs = read_csv('~/routing/data/TTS/observed_trip_lengths.csv')
observed_density = density( obs$grid_dist, weights=obs$trips/sum(obs$trips), from=0, to=47, n=516, bw=1 )

cairo_pdf('~/Dropbox/diss/routing/paper/figures/weighted-sample.pdf',width=6,height=3)
	par(mar=c(4,0,2,0),family='serif')
	plot(observed_density,main='Observed Trip Length Distribution vs. Sampled',
		  col='red',xlab='Kilometers (Manhattan Distance)',
		  bty='n',yaxt='n',ylab='',lty=2)
	lines(sample_density,col='grey',lty=2)
	# adjust weights iteratively to mimic desired distribution
	for(i in 1:15){
		adj_factor = observed_density$y / sample_density$y
		ods$weight = ods$weight * approx(x=sample_density$x,y=adj_factor,xout=ods$grid_dist,yright=0)$y
		ods$weight = ods$weight / sum(ods$weight)
		sample_density = density( ods$grid_dist, weights=ods$weight, from=0, to=47, n=516, bw=1 )
		#lines(sample_density,col=rgb(0,0,1,alpha=0.1))
	}
	# take a weighted smple of 5k OD pairs 
	samp = sample(1:nrow(ods),5000,prob=ods$weight)
	# and plot the density 
	lines(density(ods[samp,]$grid_dist,from=0, to=47, n=516, bw=1),col='blue')
dev.off()

write_csv(ods[samp,],'~/routing/data/sampled-ODs/5k-weighted-sample.csv')

remove(i,adj_factor,observed_density,sample_density,obs,samp)
gc()

