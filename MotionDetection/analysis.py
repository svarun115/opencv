import xml.etree.ElementTree as ET

tree = ET.parse('motion_output.xml')
root = tree.getroot()
videos = []

for vid in root.iter('video'):
	date = vid.find('date').text
	threshold = eval(vid.find('threshold').text)
	frames = []
	for frame in vid.findall('frame'):
		time = frame.find('time').text
		value = eval(frame.find('value').text)
		frames.append((time,value))
	time = frames[0][0]
	
	seconds = []
	motion_sum = 0

	t = frames[0][0]
	sum = 0
	count = 0 
	for i in range(len(frames)):
		if frames[i][0] == t:
			sum+=frames[i][1]
			count +=1
		else:
			if count == 0:
				continue
			avg_val = sum/count
			#append percentage of motion based on defintion of 100%
			seconds.append((t,avg_val))
			if avg_val>threshold:
				motion_sum += 1
			count = 0
			sum = 0
			t = frames[i][0]

	if count == 0:
		pass
	else: 
		if avg_val>threshold:
				motion_sum += 1
		avg_val = sum/count
		seconds.append((t,avg_val))

	
	videos.append((date,time,seconds,threshold))
	print "Date : ",date
	print "Time : ",time
	print "Threshold : ",threshold
	print "Seconds : "
	for s in seconds:
		print s
	print 
	print "Percentage of Activity over the video :{} %".format(float(motion_sum)/len(seconds)*100)
	print
	print "######################################################"
	print