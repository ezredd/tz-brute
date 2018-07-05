#!/usr/bin/env python3
# STEPS
# 0) UPDATE the function "prepare_pw" to create the candidate password following your particular logic
#    perhaps you put the first character in uppercase and add some custom suffixes at the end etc...
#    this is the place to do it!
#    here by default we do nothing
# 1) install libsodium (homebrew or other if you are under windows)
#	brew install libsodium
# 2) install pysodium (pip3)
# 	pip3 install pysodium
# 3) install pyblake2 (pip3)
#	pip3 install pyblake2
# 4) download vitalik's pybitcointools and checkout the revision before he deleted all
#    the update __PATH_TO_BITCOINTOOLS__
# 	git clone https://github.com/vbuterin/pybitcointools.git
#	cd pybitcointools
#	git checkout aeb0a2bbb8bbfe421432d776c649650eaeb882a5 .
# 5) save and decompress dictionary.tar.gz somewhere
# Example (assuming you want to restart the search from the line 100000 in each dictionary file)
# python3 dictionary.py -d '<path_dict_files>/dict.*' -s 1000000
__PATH_TO_BITCOINTOOLS__= None
__BITCOIN_FOUND__ = True

import argparse
import glob
import itertools
import logging
import math
from multiprocessing import Pool 

formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')

#[TODO] need to put this into tezos rather
try:
	import bitcoin
except:
	__BITCOIN_FOUND__ = False
	print('[WARN] bitcoin module not installed')
	pass

if not __BITCOIN_FOUND__:
	if __PATH_TO_BITCOINTOOLS__ is None:
		raise Exception('[ERRROR] bitcoin module not installed and no path provided')
	print('[INFO] try loading bitcoin from: {}'.format(__PATH_TO_BITCOINTOOLS__))
	import site
	site.addsitedir(__PATH_TO_BITCOINTOOLS__)
	import bitcoin

import tezos


def prepare_pw(word):
	'''transform dictionary word input the candidate pw, can add prefix/postfix etc...'''
	return word

def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def force_custom_dict(check_callback,dict_file,min_attempt=0,logger=None):
	if dict_file is None or dict_file == '':
		raise Exception('dictionary file not provided: dict_file={}'.format(dict_file))
	import string
	attempts = 0
	last_depth = 0
	with open(dict_file) as f:
		for word in f.readlines():
			attempts += 1
			if attempts < min_attempt:
				continue
			guess = prepare_pw(word)
			if check_callback(guess) == 1:
				msg = '[SUCCESS][{a}] guess={g}'.format(g=guess,a=attempts)
				print(msg)
				if logger is not None:
					logger.info(msg)

				return (guess, attempts)
			else:
				msg = '[FAIL][{a}] guess={g}'.format(a=attempts,g=guess)
				if logger is None:
					print(msg)
				else:
					logger.info(msg)
	return False

def job(args):		
	idx=args['idx']
	log_file = args['log_file']
	logger = setup_logger(name='logger{}'.format(idx),log_file=log_file)
	dict_file = args['dict_file']
	print('job={idx} dict_file={df} log_file={lf}'.format(
		idx=idx,
		df=dict_file,
		lf=log_file))

	def check(password):
		return tezos.check(
			args['tzadd'],
			args['mnemonic'],
			args['email'],password)

	force_custom_dict(
		check,
		args['dict_file'],
		args['minattempt'],
		logger=logger)

def main(tzadd,mnemonic,email,minattempt,dict_files):

	def check(password):
		return tezos.check(tzadd,mnemonic,email,password)

	def make_args(idx):
		return dict(
				idx=idx,
				log_file='job{}.log'.format(idx),
				dict_file=dict_files[idx],
				minattempt=minattempt,
				tzadd=tzadd,
				mnemonic=mnemonic,
				email=email
			)


	N=len(dict_files)
	if N == 1:
		force_custom_dict(check,dict_files[0],minattempt)
	else:
		print('found {} dictionary files, will spawn multiple processes'.format(N))
		p = Pool()
		args = map(make_args,range(N))
		p.map(job,args)


if __name__=='__main__':
	parser = argparse.ArgumentParser('dictionary attack based password recovery for tezos\n')
	parser.add_argument('-a','--address',help='tezos address public hash',default='tz1xxx')
	parser.add_argument('-e','--email',help='fundraiser email',default='john.doe@protonmail.com')
	parser.add_argument('-m','--mnemonic',help='fundraiser mnemonic',default='i love tacos')
	parser.add_argument('-s','--minattempt',help='restart point', default=0)
	parser.add_argument('-d','--dictfiles',help='dictionary files',required=True)
	args = parser.parse_args()
	print('using dictionary files: {}'.format(args.dictfiles))
	dict_files = sorted(glob.glob(args.dictfiles))
	minattempt = int(args.minattempt)
	main(args.address,args.mnemonic,args.email,minattempt,dict_files)

