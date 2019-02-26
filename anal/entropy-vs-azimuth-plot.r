deg2rad <- function(deg) {deg * pi / 180}
rad2deg <- function(rad) {rad * 180 / pi}

d = read.csv('~/routing/data/summary.csv')
# set the weight
gauss <- function(x){ bw = 5; return( exp(-(x**2 / ( 2 * bw**2 ) )) ) }
d$area_weight = d$o_area * d$d_area

d$dist_weight = 1

d$gauss(d$arc)

control_dens = density(
	x=c(d$azimuth-360,d$azimuth,d$azimuth+360),
	weights=rep(d$weight,3)/sum(d$weight*3),
	from=-180,to=180,n=516,bw=8
)
#var_dens = density(
#	x= c(d$azimuth-360,d$azimuth,d$azimuth+360),
#	weights=rep(d$weight,3)/sum(d$weight*3),
#	from=-180,to=180,n=516,bw=8
#)

# convert to radians and change reference point
angle  = deg2rad(-control_dens$x-90)
radius = control_dens$y * 300
# find points on a circle
x = 0.5 + radius * cos(angle)
y = 0.5 + radius * sin(angle)

plot(0,type='n',xlim=c(0,1),ylim=c(0,1),asp=1)
# draw the circle
lines(x,y)
# add lines corresponding to street grid
ew = deg2rad(17)    # east - west
ns = deg2rad(17+90) # north - south
lines(
	c( 0.5-cos(ew) , 0.5+cos(ew) ),
	c( 0.5-sin(ew) , 0.5+sin(ew) ),
	col='blue'
)
lines(
	c( 0.5-cos(ns), 0.5+cos(ns) ),
	c( 0.5-sin(ns), 0.5+sin(ns) ),
	col='blue'
)
