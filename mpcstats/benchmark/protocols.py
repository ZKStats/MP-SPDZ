# Security model
# Mod prime/GF(2^n)
# Mod 2^k
# Bin. SS
# Garbling

# exec_name, make_name, compile_flags, cflags

# Malicious, dishonest majority:
# MASCOT, LowGear, HighGear
# SPDZ2k
# Tiny, Tinier
# BMR
malicious_dishonest_majority = [t + ('MDM',) for t in [
#('mascot', 'mascot-party.x', '', ''), # ok
#('lowgear', 'lowgear-party.x', '', ''), # ok
#('highgear', 'highgear-party.x', '', ''), # ok
#('spdz2k', 'spdz2k-party.x', '--ring 128', '-DRING_SIZE=128'), # not working
#('tiny', 'tiny-party.x', '', ''), # binary circuit only
#('tinier', 'tinier-party.x', '', ''), # binary circuit only
# bmr
]]

# CowGear, ChaiGear,
# N/A,
# N/A,
# N/A
covert_dishonest_majority = [t + ('CDM',) for t in [
#('cowgear', 'cowgear-party.x', '', ''), # ok
#('chaigear', 'chaigear-party.x', '', ''), # ok
]]

# Semi, Hemi, Temi, Soho
# Semi2k
# SemiBin
# Yao's GC, BMR
semi_honest_dishonest_majority = [t + ('SHDM',) for t in [
#('semi', 'semi-party.x', '', ''), # ok
#('hemi', 'hemi-party.x', '', ''), # ok
#('temi', 'temi-party.x', '', ''), # ok
#('soho', 'soho-party.x', '', ''), # ok
('semi2k', 'semi2k-party.x', '--ring 128', ''), # ok
#('semi-bin', 'semi-bin-party.x', '', ''), # binary circuit only
#('yao', 'yao-party.x', '', ''), # binary circuit only
# bmr
]]

# Shamir, Rep3, PS, SY
# Brain, Rep3, PS, SY
# Rep3, CCD, PS
# BMR
malicious_honest_majority = [t + ('MHM',) for t in [
#('', 'brain-party.x', '', ''),
]]
 
# Shamir, ATLAS, Rep3
# Rep3
# Rep3, CCD
# BMR
semi_honest_honest_majority = [t + ('SHHM',) for t in [
#('', 'atlas-party.x', '', ''),
]]

# Rep4
# Rep4
# Rep4
# N/A
malicious_honest_supermajority = [t + ('MHS',) for t in [
]]

# Dealer
# Dealer
# Dealer
# N/A
semi_honest_dealer = [t + ('SHD',) for t in [
]]

all_protocols = malicious_dishonest_majority + covert_dishonest_majority + semi_honest_dishonest_majority + malicious_honest_majority + semi_honest_honest_majority + malicious_honest_supermajority + semi_honest_dealer

