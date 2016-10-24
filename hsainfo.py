#!/usr/bin/python3
# Copyright 2016 Advanced Micro Devices, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE COPYRIGHT HOLDER(S) OR AUTHOR(S) BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import ctypes
import ctypes.util
import os

args = {}

# Define HSA related constant borrowed from C header file
HSA_DEVICE_TYPE_GPU = 1

HSA_AGENT_INFO_NAME = 0
HSA_AGENT_INFO_VENDOR_NAME = 1
HSA_AGENT_INFO_FEATURE = 2
HSA_AGENT_INFO_MACHINE_MODEL = 3
HSA_AGENT_INFO_PROFILE = 4
HSA_AGENT_INFO_DEVICE = 17


HSA_AMD_AGENT_INFO_BDFID = 0xA006
HSA_AMD_AGENT_INFO_CHIP_ID = 0xA000


HSA_REGION_INFO_SEGMENT = 0
HSA_REGION_INFO_GLOBAL_FLAGS = 1
HSA_REGION_INFO_SIZE = 2
HSA_REGION_INFO_ALLOC_MAX_SIZE = 4
HSA_REGION_INFO_RUNTIME_ALLOC_ALLOWED = 5
HSA_REGION_INFO_RUNTIME_ALLOC_GRANULE = 6
HSA_REGION_INFO_RUNTIME_ALLOC_ALIGNMENT = 7

HSA_AMD_REGION_INFO_HOST_ACCESSIBLE = 0xA000
HSA_AMD_REGION_INFO_BASE = 0xA001
HSA_AMD_REGION_INFO_BUS_WIDTH = 0xA002


HSA_REGION_SEGMENT_GLOBAL = 0
HSA_REGION_SEGMENT_READONLY = 1
HSA_REGION_SEGMENT_PRIVATE = 2
HSA_REGION_SEGMENT_GROUP = 3


# Define map to convert id to string
hsa_segment_name = { 	 HSA_REGION_SEGMENT_GLOBAL : "HSA_REGION_SEGMENT_GLOBAL" ,
			HSA_REGION_SEGMENT_READONLY : "HSA_REGION_SEGMENT_READONLY",
			HSA_REGION_SEGMENT_PRIVATE : "HSA_REGION_SEGMENT_PRIVATE",
			HSA_REGION_SEGMENT_GROUP : "HSA_REGION_SEGMENT_GROUP"
			}



HSA_AMD_MEMORY_POOL_INFO_SEGMENT = 0
HSA_AMD_MEMORY_POOL_INFO_GLOBAL_FLAGS = 1
HSA_AMD_MEMORY_POOL_INFO_SIZE = 2
HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_ALLOWED = 5
HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_GRANULE = 6
HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_ALIGNMENT = 7
HSA_AMD_MEMORY_POOL_INFO_ACCESSIBLE_BY_ALL = 15


HSA_AMD_SEGMENT_GLOBAL = 0
HSA_AMD_SEGMENT_READONLY = 1
HSA_AMD_SEGMENT_PRIVATE = 2
HSA_AMD_SEGMENT_GROUP = 3

# Define map to convert id to string
hsa_amd_segment_name = { HSA_AMD_SEGMENT_GLOBAL : "HSA_AMD_SEGMENT_GLOBAL" ,
			HSA_AMD_SEGMENT_READONLY : "HSA_AMD_SEGMENT_READONLY",
			HSA_AMD_SEGMENT_PRIVATE : "HSA_AMD_SEGMENT_PRIVATE",
			HSA_AMD_SEGMENT_GROUP : "HSA_AMD_SEGMENT_GROUP"
			}

# Load HSA RT library
hsalibpath = ctypes.util.find_library("hsa-runtime64")

if hsalibpath == None:
	hsalibpath = "/opt/hsa/lib/libhsa-runtime64.so"

try:
	hsa = ctypes.CDLL(hsalibpath)
except:
	hsalibpath = os.environ.get('HOME') + "/git/compute/out/lib/libhsa-runtime64.so"
	hsa = ctypes.CDLL(hsalibpath)

# Define HSA RT API prototypes to use from python
agents_callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_long, ctypes.c_void_p)

hsa.hsa_agent_get_info.argtypes = [ctypes.c_long, ctypes.c_int, ctypes.c_void_p]
hsa.hsa_agent_get_info.restype = ctypes.c_int

regions_callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_long, ctypes.c_void_p)

hsa.hsa_region_get_info.argtypes = [ctypes.c_long, ctypes.c_int, ctypes.c_void_p]
hsa.hsa_region_get_info.restype = ctypes.c_int


pools_callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_long, ctypes.c_void_p)
hsa.hsa_amd_memory_pool_get_info.argtypes = [ctypes.c_long, ctypes.c_int, ctypes.c_void_p]
hsa.hsa_amd_memory_pool_get_info.restype = ctypes.c_int


class pci_bdf(ctypes.Structure):
	_fields_ = [("function", ctypes.c_uint, 3),
		("device",    ctypes.c_uint, 5),
		("bus",       ctypes.c_uint, 8),
		("unused",    ctypes.c_uint, 16)
		]


class region_global_flags(ctypes.Structure):
	_fields_ = [("HSA_REGION_GLOBAL_FLAG_KERNARG", ctypes.c_uint, 1),
		("HSA_REGION_GLOBAL_FLAG_FINE_GRAINED", ctypes.c_uint, 1),
		("HSA_REGION_GLOBAL_FLAG_COARSE_GRAINED",    ctypes.c_uint, 1)
		]

class amd_pool_global_flags(ctypes.Structure):
	_fields_ = [("HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_KERNARG_INIT", ctypes.c_uint, 1),
		("HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_FINE_GRAINED", ctypes.c_uint, 1),
		("HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_COARSE_GRAINED",    ctypes.c_uint, 1)
		]


# Globals to store informations
hsa_agents = []
memory_regions = {}
amd_pools = {}
current_agent_handle = 0


class region_info(object):
	def __init__(self, region_handle):
		self.region_handle = region_handle

		self.segment = ctypes.c_int(0xff)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_SEGMENT,
					ctypes.pointer(self.segment))

		self.size = ctypes.c_longlong(0)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_SIZE,
					ctypes.pointer(self.size))

		self.global_flags = region_global_flags()
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_GLOBAL_FLAGS,
					ctypes.pointer(self.global_flags))

		self.alloc_max_size = ctypes.c_longlong(0)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_ALLOC_MAX_SIZE,
					ctypes.pointer(self.alloc_max_size))

		self.alloc_allowed = ctypes.c_long(0)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_RUNTIME_ALLOC_ALLOWED,
					ctypes.pointer(self.alloc_allowed))

		self.alloc_granule = ctypes.c_long(0)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_RUNTIME_ALLOC_GRANULE,
					ctypes.pointer(self.alloc_granule))

		self.alloc_alignment = ctypes.c_long(0)
		hsa.hsa_region_get_info(region_handle, HSA_REGION_INFO_RUNTIME_ALLOC_ALIGNMENT,
					ctypes.pointer(self.alloc_alignment))

		self.host_accessible  = ctypes.c_long(0)
		hsa.hsa_region_get_info(region_handle, HSA_AMD_REGION_INFO_HOST_ACCESSIBLE,
					ctypes.pointer(self.host_accessible))

		self.info_base  = ctypes.c_longlong(0)
		hsa.hsa_region_get_info(region_handle, HSA_AMD_REGION_INFO_BASE,
					ctypes.pointer(self.info_base))

		self.info_bus_width  = ctypes.c_long(0)
		hsa.hsa_region_get_info(region_handle, HSA_AMD_REGION_INFO_BUS_WIDTH,
					ctypes.pointer(self.info_bus_width))

	def alloc_allowed(self):
		return self.alloc_allowed

	def is_global(self):
		if self.segment.value == HSA_REGION_SEGMENT_GLOBAL:
			return True
		else:
			return False

	def print_info(self):
		print("Region segment: %s (%d)" %
			(hsa_segment_name[self.segment.value],
			self.segment.value))

		print("Size 						%.02f MB / %.02f GB" %
			(self.size.value / (1024*1024),
			self.size.value / (1024*1024 * 1024)
			))

		if not args.verbose:
			return

		if self.is_global():
			print("Region Global flags:")
			print("         HSA_REGION_GLOBAL_FLAG_KERNARG		 %d"  %
				(self.global_flags.HSA_REGION_GLOBAL_FLAG_KERNARG))

			print("         HSA_REGION_GLOBAL_FLAG_FINE_GRAINED     %d"  %
				(self.global_flags.HSA_REGION_GLOBAL_FLAG_FINE_GRAINED))

			print("         HSA_REGION_GLOBAL_FLAG_COARSE_GRAINED   %d"  %
				(self.global_flags.HSA_REGION_GLOBAL_FLAG_COARSE_GRAINED))


		if not self.alloc_allowed:
			print("Allocation is not allowed")
		else:
			print("Allocation granularity			0x%x" %
				self.alloc_granule.value)
			print("Alignment 				0x%x" %
				self.alloc_alignment.value)
			print("Host accessible   			%d"  %
				self.host_accessible.value)


def region_callback(region_handle, ignore):
	reg = region_info(region_handle)
	if not current_agent_handle in memory_regions:
		memory_regions[current_agent_handle] = []
	memory_regions[current_agent_handle].append(reg)
	return 0


class pool_info(object):
	def __init__(self, pool_handle):
		self.pool_handle = pool_handle

		self.amd_segment = ctypes.c_int(0xff)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_SEGMENT,
					ctypes.pointer(self.amd_segment))

		self.amd_global_flags = amd_pool_global_flags()
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_GLOBAL_FLAGS,
					ctypes.pointer(self.amd_global_flags))

		self.pool_size = ctypes.c_long(0)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_SIZE,
					ctypes.pointer(self.pool_size))

		self.alloc_allowed = ctypes.c_long(0)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_ALLOWED,
					ctypes.pointer(self.alloc_allowed))

		self.alloc_granule = ctypes.c_long(0)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_GRANULE,
					ctypes.pointer(self.alloc_granule))

		self.alloc_alignment = ctypes.c_long(0)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_RUNTIME_ALLOC_ALIGNMENT,
					ctypes.pointer(self.alloc_alignment))

		self.accessible_by_all  = ctypes.c_long(0)
		hsa.hsa_amd_memory_pool_get_info(pool_handle, HSA_AMD_MEMORY_POOL_INFO_ACCESSIBLE_BY_ALL,
					ctypes.pointer(self.accessible_by_all))

	def alloc_allowed(self):
		return self.alloc_allowed

	def is_global(self):
		if self.amd_segment.value == HSA_AMD_SEGMENT_GLOBAL:
			return True
		else:
			return False

	def print_info(self):
		print("AMD pool segment: %s (%d)" %
			(hsa_amd_segment_name[self.amd_segment.value],
			self.amd_segment.value))


		print("Size						%.02f MB / %.02f GB" %
			(self.pool_size.value / (1024*1024),
			self.pool_size.value / (1024*1024 * 1024)
			))

		if not args.verbose:
			return

		if self.is_global():
			print("Pool Global flags:")
			print("         HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_KERNARG_INIT     %d"  %
				(self.amd_global_flags.HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_KERNARG_INIT))

			print("         HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_FINE_GRAINED     %d"  %
				(self.amd_global_flags.HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_FINE_GRAINED))

			print("         HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_COARSE_GRAINED   %d"  %
				(self.amd_global_flags.HSA_AMD_MEMORY_POOL_GLOBAL_FLAG_COARSE_GRAINED))

		if not self.alloc_allowed:
			print("Allocation is not allowed")
		else:
			print("Allocation granularity			0x%x" %
				self.alloc_granule.value)
			print("Alignment 				0x%x" %
				self.alloc_alignment.value)
			print("Accessible by all			%d"  %
				self.accessible_by_all.value)

def amd_pool_callback(pool_handle, ignore):
	reg = pool_info(pool_handle)
	if not current_agent_handle in amd_pools:
		amd_pools[current_agent_handle] = []
	amd_pools[current_agent_handle].append(reg)
	return 0

class agent_info(object):
	def __init__(self, agent_handle):
		self.agent_handle = agent_handle

		self.agent_name =  ctypes.create_string_buffer(256)
		hsa.hsa_agent_get_info(agent_handle, HSA_AGENT_INFO_NAME, self.agent_name)

		self.vendor_name =  ctypes.create_string_buffer(256)
		hsa.hsa_agent_get_info(agent_handle, HSA_AGENT_INFO_VENDOR_NAME, self.vendor_name)

		self.device_type = ctypes.c_int(0xff)
		hsa.hsa_agent_get_info(agent_handle, HSA_AGENT_INFO_DEVICE,
					ctypes.pointer(self.device_type))

		if  self.device_type.value == HSA_DEVICE_TYPE_GPU:
			self.pci_bdfb = pci_bdf()
			hsa.hsa_agent_get_info(agent_handle, HSA_AMD_AGENT_INFO_BDFID,
					ctypes.pointer(self.pci_bdfb))

			self.chipid = ctypes.c_int(0)
			hsa.hsa_agent_get_info(agent_handle, HSA_AMD_AGENT_INFO_CHIP_ID,
						ctypes.pointer(self.chipid))

		regions_callback_func = regions_callback_type(region_callback)
		hsa.hsa_agent_iterate_regions(agent_handle, regions_callback_func,
						ctypes.c_void_p(0));

		amd_pools_callback_func = regions_callback_type(amd_pool_callback)
		hsa.hsa_amd_agent_iterate_memory_pools(agent_handle, amd_pools_callback_func,
					ctypes.c_void_p(0));

	def is_gpu(self):
		if  self.device_type.value == HSA_DEVICE_TYPE_GPU:
			return True
		else:
			return False

	def print_info(self):

		if self.is_gpu():
			print("GPU Agent    : '%s'" % (self.agent_name.value.decode("utf-8")))
		else:
			print("CPU Agent    : '%s'" % (self.agent_name.value.decode("utf-8")))

		print("     Vendor  : '%s'" %  (self.vendor_name.value.decode("utf-8")))
		if self.is_gpu():
			print("     Device  topology    PCI [B#%02x D#%02x F#%02x]" %
				(self.pci_bdfb.bus, self.pci_bdfb.device,
				self.pci_bdfb.function))

		if args.segments  == True:
			print("(**) Regions")
			global_index = 0
			if self.agent_handle in memory_regions:
				for r in memory_regions[self.agent_handle]:
					if r.is_global():
						print("(***) Global region index ............%d" % (global_index))
						r.print_info()
						global_index = global_index + 1
					elif args.nonglobal:
						print("(***) Non global region ..............")
						r.print_info()
		print("(**) AMD Pools")
		global_index = 0
		if self.agent_handle in amd_pools:
			for p in amd_pools[self.agent_handle]:
				if p.is_global():
					print("(***) Global pool index ............%d" % (global_index))
					p.print_info()
					global_index = global_index + 1
				elif args.nonglobal:
					print("(***) Non global pool..............")
					p.print_info()




def agent_callback(agent_handle, ignore):
	global current_agent_handle
	current_agent_handle = agent_handle
	agent = agent_info(agent_handle)
	hsa_agents.append(agent)
	return 0

def check_rdma():
	try:
		with open("/sys/module/amdp2p/initstate", 'r') as f:
			read_data = f.read()
			if read_data.find("live") != -1:
				return  True
	except:
		pass

	try:
		with open("/proc/kallsyms", 'r') as f:
			read_data = f.read()
			if read_data.find(" amdkfd_query_rdma_interface") != -1:
				return True
	except:
		pass

	return False

def check_peerdirect():
	try:
		with open("/proc/kallsyms", 'r') as f:
			read_data = f.read()
			if read_data.find(" ib_register_peer_memory_client") != -1:
				return True
	except:
		pass

	return False

#
# Main logic
#
if __name__ == "__main__":
	import sys
	import argparse
	print("**************************************************************************")
	print("* Display information about HSA agents and related memory")
	print("* Version 1.00")
	print("**************************************************************************")
	parser  = argparse.ArgumentParser()
	parser.add_argument('--segments', action='store_true', default = False,
				help = "Display information about segments (Default: pool only)")
	parser.add_argument('--nonglobal', action='store_true', default = False,
				help = "Display information about non-global memory (Default: global only)")
	parser.add_argument('--verbose', action='store_true', default = False,
				help = "Display more information")
	args = parser.parse_args()
	print("Use '%s --help' for command line options" % sys.argv[0]);
	print("\n")

	agent_callback_func = agents_callback_type(agent_callback)

	hsa.hsa_init()
	hsa.hsa_iterate_agents(agent_callback_func, ctypes.c_void_p(0))

	index = 0
	for a in hsa_agents:
		print("(*) Agent index ...................................... %d" % (index))
		a.print_info()
		print("")
		index = index + 1
	hsa.hsa_shut_down()
	print("(*) System information:")

	if check_rdma():
		print("RDMA is supported by amdkfd")
	else:
		print("RDMA is not supported")

	if check_peerdirect():
		print("PeerDirect interface is detected")
	else:
		print("PeerDirect interface is not found")

