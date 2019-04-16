#######################
# read in OD level data
#######################
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
remove(fname,period)


# add extra variables to OD pairs
meta = read_csv('~/routing/data/sampled-ODs/all.csv')
# clean up the data and/or convert to factors
ods = ods %>% 
	left_join( meta ) %>% 
	mutate(
		pair = factor(paste0(o,'->',d)),
		# order periods factor by time
		period = ordered(period,levels=c('am-peak','midday','pm-peak','evening')),
		#weight = (o_area*d_area) / sum(o_area*d_area),
		from_grid = apply(cbind(-(azimuth+17)%%90,(azimuth+17)%%90),1,min)
	) %>%
	select(period,pair,everything(),-o,-d,-i,-arc,-azimuth) %>%
	arrange(pair,period)
remove(meta)

# plot distance distributions
obs = read_csv('~/routing/data/TTS/observed_trip_lengths.csv')
pop = read_csv('~/routing/data/sampled-ODs/all.csv')
cairo_pdf('~/Dropbox/diss/routing/paper/figures/sample-dist.pdf',width=6,height=3)
	par(mar=c(4,0,2,0),family='serif')
	plot(0,type='n',main='Sample vs. Empirical Trip Lengths',
		  xlab='Kilometers (Manhattan Distance)',
		  bty='n',yaxt='n',ylab='',
		  xlim=c(0,40),ylim=c(0,.09))
	# plot the sample density
	lines(
		density( ods$grid_dist, from=0, to=47, n=516, bw=1 ),
		col='red',lty=1
	)
	# plot the empirical density
	lines(
		density( obs$grid_dist, weights=obs$trips/sum(obs$trips), from=0, to=47, n=516, bw=1 ),
		col='blue',lty=2
	)
	# plot the sample population density
	lines(
		density( pop$grid_dist, from=0, to=47, n=516, bw=1 ),
		col='gray',lty=2
	)
dev.off()

remove(obs,pop)
gc()
