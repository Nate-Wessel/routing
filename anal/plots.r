library('data.table')
d = fread('~/routing/data/test.csv')
d$jf = d$depart
# SELECT EXTRACT(epoch from '2017-11-10 20:00:00-05'::timestamptz)
st = data.table( jf = seq(1509966000,1510362000,by=60) )
# nov 6th 6am to 8pm EST
cairo_pdf('~/Dropbox/diss/routing/paper/figures/12-316.pdf',width=10,height=4)
	plot(0,type='n',xlim=c(1509966000,1510016400),ylim=c(60,0))
	ci = 1 # count index
	letters = c('a','b','c')
	for( i in unique(d$itinerary) ){
		print(i)
		mtext(i,line=ci,col=rainbow(3)[ci])
		j = d[itinerary==i][st,on='jf',roll=-Inf]
		lines( 
			x=j$jf, 
			y=(j$arrive-j$jf)/60, # travel time in minutes
			col=rainbow(3)[ci] 
		)
		# assign total travel times to lettered columns
		# per each sample time
		st[,letters[ci]] = (j$arrive-j$jf)/60 # minutes
		# increment counter
		ci = ci + 1
	}
	for(letter in letters){
		next
	}
	threshold = 5 # minutes
	# better than on top
	ai = st$a - st$b < -threshold & st$a - st$c < -threshold
	bi = st$b - st$a < -threshold & st$b - st$c < -threshold
	ci = st$c - st$a < -threshold & st$c - st$b < -threshold
	
	points( x=st$jf[ai], y=rep(0,sum(ai)), col=rainbow(3)[1], pch=20 )
	points( x=st$jf[bi], y=rep(0,sum(bi)), col=rainbow(3)[2], pch=20 )
	points( x=st$jf[ci], y=rep(0,sum(ci)), col=rainbow(3)[3], pch=20 )
	
	# worse than on bottom
	ai = st$a - st$b > threshold & st$a - st$c > threshold
	bi = st$b - st$a > threshold & st$b - st$c > threshold
	ci = st$c - st$a > threshold & st$c - st$b > threshold
	
	points( x=st$jf[ai], y=rep(60,sum(ai)), col=rainbow(3)[1], pch=20 )
	points( x=st$jf[bi], y=rep(60,sum(bi)), col=rainbow(3)[2], pch=20 )
	points( x=st$jf[ci], y=rep(60,sum(ci)), col=rainbow(3)[3], pch=20 )
dev.off()
