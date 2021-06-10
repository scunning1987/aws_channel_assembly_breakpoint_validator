import requests
import re
import sys
import json
import logging
import xmltodict

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Create Console Handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# add the handlers to the logger
LOGGER.addHandler(ch)

def user_input_manifest():

    received_good_input = False
    while received_good_input == False:
        # Get user input for Manifest location
        manifest_location = input("Please enter the location of the DASH manifest:")

        # Tell this back to user and get them to confirm all is well or exit
        manifest_challenge = input("You entered %s for the manifest location, is this correct? [Y,N]" % (manifest_location))

        received_good_input = bool(re.search("[Yy]{1}", manifest_challenge))

    if ".mpd" not in manifest_location:
        #sys.exit("You did not give a valid DASH manifest URL, please run the script again")
        raise Exception("You did not give a valid DASH manifest URL, please run the script again")

    return manifest_location

def user_input_breakpoints():

    received_good_input = False
    while received_good_input == False:
        # Get user input for desired break points
        desired_bp_string = input("Enter your desired breakpoints, in seconds. Separated by comma's. IE: 30,60,90,150,240 :")

        # Tell this back to user and get them to confirm all is well or exit
        bp_challenge = input("You entered %s for the desired breakpoints, is this correct? [Y,N]" % (desired_bp_string))

        received_good_input = bool(re.search("[Yy]{1}", bp_challenge))

    # Convert user input to list
    desired_bp_list = desired_bp_string.split(",")

    bp_errors = []
    if len(desired_bp_list) > 0:
        for bp in desired_bp_list:
            if bool(re.search("[aA-zZ]", bp)) == True:
                bp_errors.append(bp)
    else:
        #sys.exit("please enter a list of valid breakpoints")
        raise Exception("please enter a list of valid breakpoints")

    if len(bp_errors) > 0:
        #sys.exit("invalid breakpoint value entered: %s " % (str(bp_errors)))
        raise Exception("invalid breakpoint value entered: %s " % (str(bp_errors)))
    else:
        return desired_bp_list

def getManifest(manifest):
    mpd_xml = requests.get(url = manifest)
    if mpd_xml.status_code != 200:
        #sys.exit("Unable to get error message, got http code : %s " % (str(mpd_xml.status_code)))
        raise Exception("Unable to get error message, got http code : %s " % (str(mpd_xml.status_code)))

    #mpd_xml_live = mpd_xml.text.replace("\n"," ")
    return xmltodict.parse(mpd_xml.text) #_live)

# Run user input sub-functions that include error checks
manifest = user_input_manifest()
breakpoint_s = user_input_breakpoints()

LOGGER.info("Successfully received manifest location and desired breakpoints")
LOGGER.info("Manifest URL : %s " % (manifest))
LOGGER.info("BreakPoints : %s " % (breakpoint_s))

# Get the DASH Manifest and transform to JSON
dash_mpd_json = getManifest(manifest)

LOGGER.debug(json.dumps(dash_mpd_json))

LOGGER.info("Manifest Parser and Timeline Calculator: Starting...")

manifest_modify_exceptions = []
manifest_modify_exceptions.clear()
adaptation_set_dict = dict()
### Modify at the MPD Level Here ### START
# EXAMPLE : dash_mpd_json['MPD']['@attribute'] == XX

### Modify at the MPD Level Here ### END

if isinstance(dash_mpd_json['MPD']['Period'], list):
    periods = len(dash_mpd_json['MPD']['Period'])
    LOGGER.debug("Manifest Modifier: Manifest has %s Periods" % (str(periods)))
    p_layout = "m"
else:
    periods = 1
    LOGGER.debug("Manifest Modifier: Manifest has %s Periods" % (str(periods)))
    p_layout = "s"
### PERIOD
for period in range(0,periods):
    if p_layout == "s":
        p = dash_mpd_json['MPD']['Period']
    else:
        p = dash_mpd_json['MPD']['Period'][period]

    ### Modify at the Period Level Here ### START
    ## p['attribute']

    ### Modify at the Period Level Here ### END

    ### ADAPTATION SET
    if isinstance(p['AdaptationSet'], list):
        adaptationsets = len(p['AdaptationSet'])
        LOGGER.debug("Manifest Modifier: Period %s has %s AdaptationSets" % (str(period),str(adaptationsets)))
        a_layout = "m"
    else:
        adaptationsets = 1
        a_layout = "s"
    for adaptationset in range(0,adaptationsets):
        LOGGER.debug("Manifest Modifier: Iterating through AS %s " % (str(adaptationset)))
        if a_layout == "s":
            a = p['AdaptationSet']
        else:
            a = p['AdaptationSet'][adaptationset]

        ### Modify at the AdaptationSet Level Here ### START
        ## a['attribute']

        adaptation_set_name = str(adaptationset) + "_" + a['@mimeType']
        adaptation_set_dict[adaptation_set_name] = {}


        ### Modify at the AdaptationSet Level Here ### END


        ### REPRESENTATION ###
        if isinstance(a['Representation'], list):
            representations = len(a['Representation'])
            LOGGER.debug("Manifest Modifier: AdaptationSet %s has %s Representations" % (str(adaptationset),str(representations)))
            r_layout = "m"
        else:
            representations = 1
            LOGGER.debug("Manifest Modifier: AdaptationSet %s has %s Representations" % (str(adaptationset),str(representations)))
            r_layout = "s"
        for representation in range(0,representations):
            LOGGER.debug("Manifest Modifier: Iterating through Representation %s " % (str(representation)))
            if r_layout == "s":
                r = a['Representation']
            else:
                r = a['Representation'][representation]

            ### Modify at the Representation Level Here ### START
            ## r['attribute']
            representation_id = r['@id']
            representation_timescale = int(r['SegmentTemplate']['@timescale'])
            if representation_id not in adaptation_set_dict[adaptation_set_name]:
                adaptation_set_dict[adaptation_set_name][representation_id] = {}
                #adaptation_set_dict[adaptation_set_name][representation_id]['timescale'] = representation_timescale

            # Process the segement timeline for the representation
            ### SEGMENT TIMELINE ###
            if isinstance(r['SegmentTemplate']['SegmentTimeline']['S'], list):
                segmenttimeline = len(r['SegmentTemplate']['SegmentTimeline']['S'])
                LOGGER.debug("Manifest Modifier: AdaptationSet %s has %s Representations" % (str(adaptationset),str(representations)))
                t_layout = "m"
            else:
                segmenttimeline = 1
                LOGGER.debug("Manifest Modifier: AdaptationSet %s has %s Representations" % (str(adaptationset),str(representations)))
                t_layout = "s"

            timeline_segments = []
            timeline_segments.clear()
            timeline_segments_ms = []
            timeline_segments_ms.clear()

            for timeline in range(0,segmenttimeline):
                LOGGER.debug("Manifest Modifier: Iterating through Segment Timeline %s " % (str(timeline)))
                if t_layout == "s":
                    t = r['SegmentTemplate']['SegmentTimeline']['S']
                else:
                    t = r['SegmentTemplate']['SegmentTimeline']['S'][timeline]

                s_time = t['@t']
                s_time_ms = round(int(s_time) / representation_timescale * 1000)
                s_dur = t['@d']
                timeline_segments.append({'t': s_time,'d': s_dur})
                timeline_segments_ms.append(s_time_ms)
                if "@r" in t:
                    for repeat in range(1,int(t['@r'])+1):
                        r_time = int(repeat) * int(s_dur) + int(s_time)
                        r_time_ms = round(int(r_time) / representation_timescale * 1000)
                        timeline_segments.append({'t': r_time,'d': s_dur})
                        timeline_segments_ms.append(r_time_ms)
            if "timeline" not in adaptation_set_dict[adaptation_set_name][representation_id]:
                adaptation_set_dict[adaptation_set_name][representation_id] = timeline_segments_ms
            else:
                adaptation_set_dict[adaptation_set_name][representation_id].update(timeline_segments_ms)
            ### Modify at the Representation Level Here ### END

# All Representations timelines are now in this dict: adaptation_set_dict , the master keys are the adaptation sets, then child key value for representation id and elapsed segment timeline

actual_breakpoints_list = []

for breakpoint in breakpoint_s:

    breakpoint_ms = int(breakpoint) * 1000

    # Get closest segment boundary from first representation of first adaptation set
    adaptation_set_1 = adaptation_set_dict[list(adaptation_set_dict.keys())[0]]
    representation_1_timeline = adaptation_set_1[list(adaptation_set_1.keys())[0]]
    LOGGER.info("Timeline from first Representation of first Adaptation Set : %s" % (representation_1_timeline))

    LOGGER.info("Trying to find aligned breakpoint at desired time: %s" % (str(breakpoint)))

    retries = 0
    segment_index = 0
    not_found_alignment = True

    while not_found_alignment and retries < 5:

        ## Now find Closest segment boundary and note the index in list
        ## OR if we're in retry mode, the segment index has already incremented by 1
        if retries == 0:
            for segment in representation_1_timeline:
                if segment < breakpoint_ms:
                    segment_index += 1

        # Protect the automatic increment for going beyond the range of the timeline list
        if segment_index >= len(representation_1_timeline):
            segment_index = len(representation_1_timeline)

        actual_breakpoint = representation_1_timeline[segment_index]
        LOGGER.info("Breakpoint at segment (0 based) : %s, cumulative duration : %s " % (segment_index,actual_breakpoint))
        LOGGER.info("Now iterating through all other Representations to see if we can use this value")

        boundary_point_exceptions = []
        boundary_point_exceptions.clear()

        LOGGER.info("Checking timelines for desired breakpoint : %s, actually looking for : %s" % (breakpoint_ms,actual_breakpoint))

        for a in adaptation_set_dict:
            LOGGER.info("Checking Adaptation Set : %s , there are %s representations" % (a,str(len(adaptation_set_dict[a]))))
            for r in adaptation_set_dict[a]:
                LOGGER.info("Checking Representation : %s" % (r))
                found_boundary_point = False
                segment_to_use = 0
                for segment in adaptation_set_dict[a][r]:
                    if segment > actual_breakpoint - 100 and segment < actual_breakpoint + 100:
                        found_boundary_point = True
                        if segment_to_use == 0:
                            segment_to_use = segment
                if found_boundary_point:
                    LOGGER.info("Found suitable boundary point, at point %s" % (segment_to_use))
                else:
                    LOGGER.warning("Unable to find boundary point for Representation Id : %s " % (r))
                    boundary_point_exceptions.append(r)

        if len(boundary_point_exceptions) > 0:
            LOGGER.warning("Unable to use the segment closest to the desired breakpoint. Trying the next segment...")
            if retries == 4:
                LOGGER.error("We're not going to continue searching for alignment on the specified breakpoint : %s " % (breakpoint))
            retries += 1
            segment_index += 1
        else:
            actual_breakpoints_list.append(actual_breakpoint)
            not_found_alignment = False

LOGGER.info("SCRIPT RUN COMPLETE: Please use these breakpoints for your asset : %s" % (actual_breakpoints_list))