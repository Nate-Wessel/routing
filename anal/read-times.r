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
			times = read.csv(fname)
			times$period = period
		}else{
			d = read.csv(fname)
			d$period = period
			times = rbind(times,d)
			remove(d)
		}
	}
}
# rename, simplify, etc
times$hour = factor(times$hour)
times$period = factor(times$period)
times$pair = factor(paste0(times$o,'->',times$d))
times$o = times$d = NULL
# add weights by OD
print('merging times with ods')
times = merge( x=times, y=ods[,c('pair','weight')], all.x=T, by='pair' )

gc()

