import pandas as pd
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

#######################################################################
#DRL - constants to use
#######################################################################

MIN_INT_OBS    = 12    # minimum intubation observation window in hours
EXCLUSION_WIN  = .0833 # length of exclusion window in hours
EXTUBATION_WIN = 6     # length of pre-extubation observation window
dataset        = 'valid'

#######################################################################
#DRL - gather the necessary vent data
#######################################################################

print 'processing vent data...'

#DRL - path to the vent data
data_path = '/mnt/Swift/Data/DRTED/DRTEDv5/DS5v4_extubation_pass/raw/o2_vent_events_concat_no_dnr_no_trach_w_truth.csv'

#DRL - read in the vent data
print '\treading in vent data...'
data = pd.read_csv(data_path)

#DRL - get the first ventilation record per encounter
print '\tgetting first vent record...'
first_inbubation_per_encounter = data.groupby('eid').first()

#DRL - filter out just the successful first intubations
print '\tfiltering out only successful extubations...'
successful_first_intubation = first_inbubation_per_encounter[first_inbubation_per_encounter['intubation_success_bool'] == True]

#DRL - change index name from eid to encounter (probably for merging later)
print '\trenaming eids to encounters...'
successful_first_intubation.index.names = ['encounter']

#DRL - reset the index back to a column (again, probably for merging)
print '\treseting vent index...'
successful_first_intubation.reset_index(inplace = True)

#######################################################################
#DRL - generate the targets from the raw (non-ffilled) data
#######################################################################

print 'processing raw data...'

#DRL - read in the validation dataset
raw_path = '/mnt/Swift/Data/DRTED/DRTEDv5/DS5v4/icu/' + dataset + 'Patients.hdf'

print '\treading in raw data (%s)...' % raw_path
raw = pd.read_hdf(raw_path)

#DRL - ffill the raw data
#       interesting the reason for not starting directly with the
#       pre-processed data was so we properly took the mean but then
#       we end up ffilling anyway /shrug
print '\tffill the raw data...'
raw = raw.groupby('encounter').ffill()

#DRL - again reset the index of raw (not sure why yet)
print '\treset the index to match convention...'
raw.reset_index(inplace = True)

#DRL - this is why -- make the merge a simple 'on' merge
#       note: this could have been donen w/ index merging
print '\tmerge the raw data with the successful intubations...'
raw_join = raw.merge(successful_first_intubation, how = 'inner', on = 'encounter')

#DRL - cast end and start as datetimes
print '\tcast start and end times to datetimes...'
raw_join['end'] = pd.to_datetime(raw_join['end'])
raw_join['start'] = pd.to_datetime(raw_join['start'])

#DRL - throw out data after extubation
print '\tfilter data after extubation...'
raw_join = raw_join[raw_join['start_time'] <= raw_join['end']]

#DRL - get relative intubation time, relative extubation time
#       and calculate the mean over the last 6 hours w/ exclusion window
print '\tcalculate int/ext relative timestamps...'
raw_join['absoluteTime_intStart'] = (raw_join['start_time'] - raw_join['start']).apply(lambda x: x.total_seconds() / 3600)
raw_join['absoluteTime_intEnd']   = (raw_join['start_time'] - raw_join['end']).apply(lambda x: x.total_seconds() / 3600)

#DRL - filter out any encounters w/o at least MIN_INT_OBS
print '\tfilter eids w/o minimum vent observations...'
obs_filter = raw_join.groupby('encounter')['absoluteTime_intStart'].max() > MIN_INT_OBS
raw_join   = raw_join.set_index('encounter').loc[obs_filter[obs_filter].index].reset_index()

#DRL - apply the exclusion and extubation windows
print '\tfilter data not w/i extubation window...'
raw_join = raw_join[raw_join['absoluteTime_intEnd'] >= -EXTUBATION_WIN]
raw_join = raw_join[raw_join['absoluteTime_intEnd'] <  -EXCLUSION_WIN]

#DRL - now the raw data is just the window we care about and we have
#       thrown out all patients w/o our minimum observation window
#       so we can calculate the mean measurement during that period
raw_join.set_index(['encounter', 'start_time'], inplace=True)

#DRL - list of targets to calculate
list_of_targets = ['Heart Rate', 'Diastolic Blood Pressure', 'Systolic Blood Pressure', 
                   #'ABG pH', 'ABG O2 sat', 'ABG PCO2', 'ABG PO2', 
                   'Respiratory Rate', 'Bicarbonate Serum']

#DRL - now generating the targets is a super simple groupby operation
print '\tcalculate our targets (yay!)...'
targets = raw_join[list_of_targets].groupby(level=0).mean()

#DRL - zmuv the target values
print '\tread in zmuv data for normalization...'
zmuv = pd.read_csv('/mnt/Swift/Data/DRTED/DRTEDv5/DS5v4/settings/zmuv_info.csv')
zmuv.set_index('event_name', inplace = True)

#DRL - perform the z normalization per target
print '\tzmuv the data...'
for x in list_of_targets:
    print '\t\tzmuving %s...' % x
    targets[x] = (targets[x] - zmuv.loc[x]['mean'])/zmuv.loc[x]['std']

#DRL - just wholesale append 'target' to the columns for convenience
targets.columns = ['target_' + x for x in targets.columns]

#DRL - add some vent columns we care about to targets for convenience
targets['start'] = raw_join.groupby(level=0)['start'].first()
targets['end']   = raw_join.groupby(level=0)['end'].first()

#DRL - reset_index to mimic the on merges below
targets.reset_index(inplace=True)

#######################################################################
#DRL - merge the targets with the preprocessed data
#######################################################################

print 'processing the training data...' 

#DRL - path to the preprocessed data
preprocessed_data_path = '/mnt/Swift/Data/DRTED/DRTEDv5/DS5v4/icu/preprocessed/' + dataset + 'Patients_zmuv_zffill.hdf'

#DRL - read in the data
print '\treading in the preprocessed data (%s)...' % preprocessed_data_path
preprocessed_data = pd.read_hdf(preprocessed_data_path)

#DRL - reset the index for merging convenience
print '\tresetting index to follow convention...'
preprocessed_data.reset_index(inplace=True)

#DRL - inner join to get int data for encounters we care about
print '\tjoining data with targets (and filtering eids)...'
preprocessed_data = preprocessed_data.merge(targets, how = 'inner', on = ['encounter'])

#######################################################################
#DRL - cull the preprocessed data and truth to the elements we want
#######################################################################

#DRL - throw out all data after extubation
print '\tremove data after extubation...'
preprocessed_data = preprocessed_data[preprocessed_data['start_time'] <= preprocessed_data['end']]

#DRL - get relative intubation time, relative extubation time
#       and calculate the mean over the last 6 hours w/ exclusion window
print '\tadding relative int/ext times for convenience...'
preprocessed_data['absoluteTime_intStart'] = (preprocessed_data['start_time'] - preprocessed_data['start']).apply(lambda x: x.total_seconds() / 3600)
preprocessed_data['absoluteTime_intEnd']   = (preprocessed_data['start_time'] - preprocessed_data['end']).apply(lambda x: x.total_seconds() / 3600)

#DRL - set the necessary target nans starting with before intubation
#       and finally for the final EXTUBATION_WIN of observation
print '\tnanify targets before intubation and during extubation obs window...'
for target in list_of_targets:
    print '\t\tnanifying %s...' % target
    preprocessed_data['target_' + target] = np.where(preprocessed_data['absoluteTime_intStart'] < 0, np.nan, preprocessed_data['target_' + target])
    preprocessed_data['target_' + target] = np.where(preprocessed_data['absoluteTime_intEnd'] > -EXTUBATION_WIN, np.nan, preprocessed_data['target_' + target])

#DRL - path to save processed data
outpath = '/mnt/Swift/Data/DRTED/DRTEDv5/DS5v4_extubation_pass/%s_Patients_zmuv_PASS_%d_minObs_%d_extWin.hdf' % (dataset, MIN_INT_OBS, EXTUBATION_WIN)

#DRL - now save the processed dataset
print 'saving completed data (%s)...' % outpath
preprocessed_data.set_index(['encounter', 'time_step'], inplace=True)
preprocessed_data.to_hdf(outpath, key = 'eid', mode = 'w')
