library('data.table')
d = fread('~/routing/data/db-trips.csv')
d$jf = d$depart # jf = join field

# define three colors for a white background
colors = c('navyblue','salmon','aquamarine3')
letters = c('a','b','c')
itins = c(
	'{w134,s3177,r47,s3184,w57,s14477,r2,s14482,w828}',
	'{w838,s9600,r506,s9614,w583}',
	'{w134,s3177,r47,s3180,w54,s9600,r506,s9614,w583}'
)

# make table of minutes spanning day
# SELECT EXTRACT(epoch from '2017-11-06 06:00:00-05'::timestamptz)
# SELECT EXTRACT(epoch from '2017-11-06 20:00:00-05'::timestamptz)
st = data.table( jf = seq(1509966000,1510016400, by=60) )

cairo_pdf('~/Dropbox/diss/routing/paper/figures/12-316-habitual.pdf',width=10,height=2.5)
	# plot only one day - nov 6th 6am to 8pm EST
	par( mar=c(2,2,3,0), family='serif', bty='n' ) # bottom, left, top, right
	plot(
		0, type='n', xlim=c(1509966000,1510016400), ylim=c(55,10),
		yaxt='n',ylab='',xaxt='n',xlab=''
	)
	# make the y axis
	marks = c(0,10,20,30,40,50,60)
	axis( 2, at=marks, las=1 )
	# make the X axis with hours
	marks = seq(1509966000,1510016400, by=3600)
	labs = paste0((marks - 1509966000 + 6*3600)/3600,':00')
	axis( 1, at=marks, labels=labs, las=1 )

	ci = 1 # color index
	for( itin in itins ){
		# rolling join into table j
		j = d[itinerary==itin][st,on='jf',roll=-Inf]
		lines( 
			x=j$jf, 
			y=(j$arrive-j$jf)/60, # travel time in minutes 
			col=colors[ci] 
		)
		# assign total travel times to lettered columns
		# per each sample time
		st[,letters[ci]] = (j$arrive-j$jf)/60 # minutes
		# print itinerary at top of plot
		itin_string = paste0( 
			letters[ci], ': ', itin, 
			' mean time:', round(mean( (j$arrive-j$jf)/60 ),2), ' minutes'
		)
		print( itin_string )
		mtext( itin_string, line=3-ci, col=colors[ci], adj=0, family='monospace' )
		# increment counter
		ci = ci + 1
	}
	
#	threshold = 5 # minutes
#	# better than on top
#	ai = st$a - st$b < -threshold & st$a - st$c < -threshold
#	bi = st$b - st$a < -threshold & st$b - st$c < -threshold
#	ci = st$c - st$a < -threshold & st$c - st$b < -threshold
	
#	points( x=st$jf[ai], y=rep(0,sum(ai)), col=colors[1], pch=20 )
#	points( x=st$jf[bi], y=rep(0,sum(bi)), col=colors[2], pch=20 )
#	points( x=st$jf[ci], y=rep(0,sum(ci)), col=colors[3], pch=20 )
	
dev.off()
