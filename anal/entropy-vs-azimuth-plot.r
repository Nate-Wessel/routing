rad2deg <- function(rad) {(rad * 180) / (pi)}
deg2rad <- function(deg) {(deg * pi) / (180)}

d = read.csv('~/routing/data/summary.csv')
control_dens = density(
	x=c(d$azimuth-360,d$azimuth,d$azimuth+360),
	from=-180,to=180,n=516,bw=10
)
var_dens = density(
	x= c(d$azimuth-360,d$azimuth,d$azimuth+360),
	weights=rep(d$retro_ent,3)/sum(d$retro_ent*3),
	from=-180,to=180,n=516,bw=10
)

# and make a simpler data structure
angle  = deg2rad(var_dens$x)
radius = var_dens$y / control_dens$y / 3
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
	c(0.5,(0.5+1*cos(ew))),
	c(0.5,(0.5+1*sin(ew))),
	col='red'
)
lines(
	c(0.5,(0.5+1*cos(ns))),
	c(0.5,(0.5+1*sin(ns))),
	col='green'
)
