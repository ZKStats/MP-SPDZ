dishonest_majority_malicious = [t + ('DM-M-SS',) for t in [
#('mascot', 'mascot-party.x', '', ''), # ok
#('mama', 'mama-party.x', '', ''), # ok
#('spdz2k', 'spdz2k-party.x', '--ring 128', '-DRING_SIZE=128'), # not working
#('lowgear', 'lowgear-party.x', '', ''), # ok
#('highgear', 'highgear-party.x', '', ''), # ok
]]

dishonest_majority_covert = [t + ('DM-C-SS',) for t in [
#('cowgear', 'cowgear-party.x', '', ''), # ok
#('chaigear', 'chaigear-party.x', '', ''), # ok
]]

dishonest_majority_semi_honest = [t + ('DM-SH-SS',) for t in [
#('semi', 'semi-party.x', '', ''), # ok
#('semi2k', 'semi2k-party.x', '--ring 128', ''), # ok
#('hemi', 'hemi-party.x', '', ''), # ok
#('temi', 'temi-party.x', '', ''), # ok
#('soho', 'soho-party.x', '', ''), # ok
]]

# Honest majority, malicious
honest_majority_malicious = [t + ('HM-M',) for t in [
#('ring', 'replicated-ring-party.x', '--ring 128', ''), # ok
#('ps-rep-ring', 'ps-rep-ring-party.x', '--ring 128', ''), # ok
#('mal-rep-ring', 'malicious-rep-ring-party.x', '--ring 128', ''), # ok
#('sy-rep-ring', 'sy-rep-ring-party.x', '--ring 128', ''), # ok
#('rep4-ring', 'rep4-ring-party.x', '--ring 128', ''), # not working
#('ps-rep-field', 'ps-rep-field-party.x', '', ''), # ok
#('sy-rep-field', 'sy-rep-field-party.x', '', ''), # ok
#('mal-rep-field', 'malicious-rep-field-party.x', '', ''), # ok
#('mal-shamir', 'malicious-shamir-party.x', '', ''), # ok
#('sy-shamir', 'sy-shamir-party.x', '', ''), # ok
]]

# Honest majority, non-malicious
honest_majority_non_malicious = [t + ('HM-NM',) for t in [
#('rep-field', 'replicated-field-party.x', '', ''), # ok
#('atlas', 'atlas-party.x', '', ''), # ok
#('shamir', 'shamir-party.x', '', ''), # ok
]]

# BMR
bmr = [t + ('BMR',) for t in [
#('real-bmr', 'real-bmr-party.x', '', ''), # ok
#('semi-bmr', 'semi-bmr-party.x', '', ''), # ok
#('shamir-bmr', 'shamir-bmr-party.x', '', ''), # ok
#('mal-shamir-bmr', 'mal-shamir-bmr-party.x', '', ''), # ok
#('rep-bmr', 'rep-bmr-party.x', '', ''), # ok
#('mal-rep-bmr', 'mal-rep-bmr-party.x', '', ''), # ok
]]

all_protocols = dishonest_majority_malicious
all_protocols += dishonest_majority_covert
all_protocols += dishonest_majority_semi_honest
all_protocols += honest_majority_malicious
all_protocols += honest_majority_non_malicious
all_protocols += bmr

