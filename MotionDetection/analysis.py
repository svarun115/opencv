import xml.etree.ElementTree as ET
from collections import Counter

tree = ET.parse('motion_output.xml')
root = tree.getroot()
# videos = []

for vid in root.iter('video'):
	date = vid.find('date').text
	threshold = eval(vid.find('threshold').text)
	frames = []
	#print len(vid.findall('frame'))
	for frame in vid.findall('frame'):
		time = frame.find('time').text
		value = eval(frame.find('value').text)
		region = eval(frame.find('region').text)
		frames.append((time,value,region))
	time = frames[0][0]
	
	seconds = []
	motion_sum = 0
	regions =[]

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
		regions.append(frames[i][2])

	if count == 0:
		pass
	else: 
		if avg_val>threshold:
				motion_sum += 1
		avg_val = sum/count
		seconds.append((t,avg_val))

	data = Counter(regions)
	area = data.most_common(1)[0][0]
	#print area 

	if area == 1:
		r = "Top Right"
	elif area == 2:
		r = "Top Left"
	elif area == 3:
		r = "Bottom left"
	else:
		r = "Bottom Right"
	
	# videos.append((date,time,seconds,threshold))
	print "Date : ",date
	print "Time : ",time
	print "Threshold : ",threshold
	print "Seconds : "
	for s in seconds:
		print s
	print 
	print "Percentage of Activity over the video :{} %".format(float(motion_sum)/len(seconds)*100)
	print
	print "Most of the activity was in {} region".format(r)
	print "######################################################"
	print