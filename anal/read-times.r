###############################################
# read in the db-estimated departure times data
###############################################
# check that we have the OD level data
if( ! exists('ods') | ! exists('periods') ){ 
	source('~/routing/anal/read-and-weight-ods.r')
}
# remove this and reread
if( exists('times') ){ remove(times) }

for( period in periods ){
	fname = paste0('~/routing/data/untracked/',period,'-times.csv')
	if( file.exists(fname) ){
		print(paste('reading',fname))
		if( ! exists('times') ){
			times = read_csv(fname)
			times$period = period
		}else{
			d = read_csv(fname)
			d$period = period
			times = bind_rows(times,d)
			remove(d)
		}
	}
}
remove(fname,period)

# rename, simplify, add fields from ods
times = times %>% 
	mutate(
		hour = factor(hour),
		period = ordered(period,levels=c('am-peak','midday','pm-peak','evening')),
		pair = factor(paste0(o,'->',d)),
		d_hab = hab - any,  # habit time delta 
		d_real = real - any # realtime time delta
	) %>%
	select(pair,period,everything(),-o,-d) %>%
	left_join( distinct(ods[,c('pair','weight','grid_dist')]) )

gc()

