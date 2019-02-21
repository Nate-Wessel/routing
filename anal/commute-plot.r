# plot the three alternative strategies for my home -> work commute

# read in the travel timees table
d = read.csv('~/routing/data/output/12->316-trips.csv',skip=6)
# clip to only one day - nov 6th 6am to 8pm EST
# SELECT EXTRACT(epoch from '2017-11-06 06:00:00-05'::timestamptz)
# SELECT EXTRACT(epoch from '2017-11-06 20:00:00-05'::timestamptz)
d = d[between(d$depart,1509966000,1510016400),]
# define three colors for a white background
colors = c('navyblue','salmon','aquamarine3')
# define itinerary names
itins = list('a: {w134,s3177,r47,s3184,w57,s14477,r2,s14482,w828}',
			 'b: {w134,s3177,r47,s3180,w54,s9600,r506,s9614,w583}',
			 'c: {w838,s9600,r506,s9614,w583}')

cairo_pdf('~/Dropbox/diss/routing/paper/figures/12-316.pdf',width=10,height=2.5)
	# plot 
	par( mar=c(2,2,3,0), family='serif', bty='n' ) # bottom, left, top, right
	plot( 0, type='n', xlim=c(1509966000,1510016400), ylim=c(60,5), yaxt='n',ylab='',xaxt='n',xlab='' )
	# make the y axis
	axis( 2, at=seq(20,70,10), las=1 )
	# make the X axis with hours
	ticks = seq(1509966000,1510016400, by=3600)
	labs = paste0((ticks - 1509966000 + 6*3600)/3600,':00')
	axis( 1, at=ticks, labels=labs, las=1 )
	# plot the lines	
	lines( x=d$depart,y=d$a,col=colors[1] )
	lines( x=d$depart,y=d$b,col=colors[2] )
	lines( x=d$depart,y=d$c,col=colors[3] )
	# print itineraries at top of plot
	itin_string = paste( itins[1],'mean time:',round(mean(d$a),2), ' minutes' )
	mtext( itin_string, line=2, col=colors[1], adj=0, family='monospace' )
	itin_string = paste( itins[2],'mean time:',round(mean(d$b),2), ' minutes' )
	mtext( itin_string, line=1, col=colors[2], adj=0, family='monospace' )
	itin_string = paste( itins[3],'mean time:',round(mean(d$c),2), ' minutes' )
	mtext( itin_string, line=0, col=colors[3], adj=0, family='monospace' )
	
	#add the choice bars
	############################
	# habit is the easiest
	segments(x0=d$depart,x1=d$depart,y0=5,y1=9,col=colors[1])
	# get just the preboarding times in a matrix
	m = as.matrix(d[,c('a_pre_board','b_pre_board','c_pre_board')])
	first_board = apply(m,1,which.min)
	segments(x0=d$depart,x1=d$depart,y0=10,y1=14,col=colors[first_board])
	# get just the travel times in a matrix
	m = as.matrix(d[,c('a','b','c')])
	fastest = apply(m,1,which.min)
	segments(x0=d$depart,x1=d$depart,y0=15,y1=19,col=colors[fastest])
	
dev.off()
