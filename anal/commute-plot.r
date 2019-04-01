# plot the three alternative strategies for my morning commute

# read in the travel times table - all five days
# covers minutes between 6-22 for five days
od = read_csv('~/routing/data/output/12->316-trips.csv',skip=4)
# add factor for days
od$day = ordered(
	rep(c('Monday','Tuesday','Wednesday','Thursday','Friday'),rep(180,5)),
	levels = c('Monday','Tuesday','Wednesday','Thursday','Friday')
)

od = od %>%
	group_by(day) %>%
	mutate( hour = 6 + row_number(depart)/60 ) %>%
	select(-depart)
	
tt = od %>% 
	gather( a,b,c,key='itinerary',value='travel_time' ) %>%
	select(-a_pre_board,-b_pre_board,-c_pre_board)

d = od %>%
	select(-a,-b,-c) %>%
	rename(a=a_pre_board,b=b_pre_board,c=c_pre_board) %>%
	gather(a,b,c,key='itinerary',value='pre_board') %>%
	inner_join(tt)

# print mean travel times per itinerary
d %>% 
	group_by(itinerary) %>%
	summarize( mtt = mean(travel_time) )

optimal_choice = 	d %>%
	# add a field for mean travel_time per itinerary
	group_by(itinerary) %>%
	summarize( mtt = mean(travel_time) ) %>% 
	inner_join(d) %>%
	# sort by travel time and then mean travel time, asc
	arrange(travel_time,mtt) %>% 
	group_by(day,hour) %>%
	slice(1) %>%
	select(itinerary,day,hour)

# entropy of optimal choice
optimal_choice %>% 
	group_by( itinerary ) %>%
	summarize( n=n() ) %>%
	mutate( p = n/sum(n) ) %>% 
	summarize( entropy = - sum(p*log(p,2)) )

realtime_choice = d %>%
	# add a field for mean travel_time per itinerary
	group_by(itinerary) %>%
	summarize( mtt = mean(travel_time) ) %>% 
	inner_join(d) %>%
	# sort by travel time and then mean travel time, asc
	arrange(pre_board,mtt) %>% 
	group_by(day,hour) %>%
	slice(1) %>%
	select(itinerary,day,hour)

cairo_pdf('~/Dropbox/diss/routing/paper/figures/12-316.pdf',width=7,height=5)
# plot of varying optimal choice over departure times
	ggplot() + 
		geom_line(
			data=d,
			aes(x=hour,y=travel_time,color=itinerary),size=0.25
		) + 
		geom_segment(
			data=optimal_choice,
			aes(x=hour,y=10,xend=hour,yend=15,color=itinerary),size=1.1
		) + 
		geom_segment(
			data=realtime_choice,
			aes(x=hour,y=0,xend=hour,yend=5,color=itinerary),size=1.1
		) +
		scale_color_manual(values=c('navyblue','salmon','aquamarine3','deeppink2','goldenrod')) + 
		facet_grid(day~.) + 
		theme_minimal() + 
		labs(y='Travel Time (Minutes)',x='Time (AM)')
dev.off()
