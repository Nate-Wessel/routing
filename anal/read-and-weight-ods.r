##########################################################
# read in OD level data and assign weights to observations
##########################################################
library(tidyverse)
if( exists('ods') ){ remove(ods) }
# read in the OD pairs
periods = c('am-peak','midday','pm-peak','evening')
# periods will be weighted evenly though they have different durations: 3,6,4,3 hours 
for( period in periods ){
	fname = paste0('~/routing/data/untracked/',period,'-od-stats.csv')
	if( file.exists(fname) ){
		print(paste('reading',fname))
		if( ! exists('ods') ){
			ods = read_csv(fname)
			ods$period = period
		}else{
			d = read_csv(fname)
			d$period = period
			ods = bind_rows(ods,d)
			remove(d)
		}
	}
}
# clean up the data and/or convert to factors
ods$pair = factor(paste0(ods$o,'->',ods$d))
ods$period = factor(ods$period)
ods$o = ods$d = ods$i = ods$arc = NULL
# assign weights based on areas
ods$weight = (ods$o_area*ods$d_area) / sum(ods$o_area*ods$d_area)
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
remove(i,adj_factor,observed_density,sample_density,obs,fname,period)
gc()
