"""Translate basis info from CP2K calculation to SALTED basis info"""

import argparse
from itertools import islice
from typing import Dict, Tuple

import inp
import numpy as np

from salted.basis_client import (
    BasisClient,
    SpeciesBasisData,
)

from salted.get_basis_info import get_parser


def build(dryrun: bool = False, force_overwrite: bool = False):
    """Scheme: parse all basis data (.dat files) in the working directory,
    update the basis_data dict,
    and write to the database when all species are recorded.
    """
    assert inp.qmcode.lower() == "cp2k", f"{inp.qmcode=}, but expected 'cp2k'"

    """Run Andrea's code"""
    lmax, nmax, alphas = parse_files_basis_info(inp.species, inp.dfbasis)

    """Convert to basis_client format"""
    basis_data: Dict[str, SpeciesBasisData] = {}
    for spe in lmax.keys():
        assert lmax[spe] + 1 == len(
            [i for i in nmax.keys() if i[0] == spe]
        ), f"{lmax=}, {nmax=}"  # compare l_list with n_list
        basis_data[spe] = {
            "lmax": lmax[spe],
            "nmax": [nmax[(spe, l)] for l in range(lmax[spe] + 1)],
        }

    """write to files"""
    if dryrun:
        print("Dryrun mode, not writing to the database")
        print(f"{inp.species=}")
        print(f"{inp.dfbasis=}")
        print(f"{lmax=}, {nmax=}")
        print(f"{basis_data=}")
        print(f"{alphas=}")
    else:
        for spe in inp.species:
            for l in range(lmax[spe] + 1):
                np.savetxt(f"{spe}-{inp.dfbasis}-alphas-L{l}.dat", alphas[(spe, l)])
                # np.savetxt(spe+"-"+inp.dfbasis+"-contraction-coeffs-L"+str(l)+".dat",contra[(spe,l)])
        BasisClient().write(inp.dfbasis, basis_data, force_overwrite)


def parse_files_basis_info(species, dfbasis) -> (
    Tuple[Dict[str, int], Dict[Tuple[str, int], int], Dict[Tuple[str, int], np.ndarray]]
):
    """Parse the basis files of cp2k
    File naming convention: `[species]-[basis_name]`.
    No file IO here, just parsing the data.

    This function is copied from the original implementation in `salted/aims/get_basis_info.py`,
    see https://github.com/andreagrisafi/SALTED/blob/8f686cda/example/Au100-CP2K/get_basis_info.py
    """

    # npgf = {}
    lmax = {}
    nmax = {}
    alphas = {}
    contra = {}
    # fbasis = open("new_basis_entry", "w+")
    # fbasis.write('   if basis=="' + dfbasis + '":\n\n')
    for spe in species:
        lmaxlist = []
        alphalist = {}
        for l in range(10):
            # nmax[(spe, l)] = 0
            alphalist[l] = []
        with open(spe + "-" + dfbasis) as f:
            for line in f:
                nsets = int(list(islice(f, 1))[0])
                for iset in range(nsets):
                    line = list(islice(f, 1))[0]
                    llmin = int(line.split()[1])
                    llmax = int(line.split()[2])
                    nnpgf = int(line.split()[3])
                    nmaxtemp = {}
                    for l in range(llmin, llmax + 1):
                        lmaxlist.append(l)
                        nmaxtemp[l] = int(line.split()[4 + l - llmin])
                        # nmax[(spe, l)] += nmaxtemp[l]
                        nmax[(spe, l)] = nmax.get((spe, l), 0) + nmaxtemp[l]
                        alphalist[l].append(np.zeros(nnpgf))
                        contra[(spe, l)] = np.zeros((nmaxtemp[l], nnpgf))
                    lines = list(islice(f, nnpgf))
                    for ipgf in range(nnpgf):
                        line = lines[ipgf].split()
                        alpha = float(line[0])
                        icount = 0
                        for l in range(llmin, llmax + 1):
                            alphalist[l][-1][ipgf] = alpha
                            for n in range(nmaxtemp[l]):
                                contra[(spe, l)][n, ipgf] = line[1 + icount]
                                icount += 1
                break
        lmax[spe] = max(lmaxlist)
        print("L_max = ", lmax[spe])
        for l in range(lmax[spe] + 1):
            alphas[(spe, l)] = np.array(alphalist[l]).flatten()

    return lmax, nmax, alphas


if __name__ == "__main__":
    print("Please call `python -m salted.get_basis_info` instead of this file")

    parser = get_parser()
    args = parser.parse_args()

    build(dryrun=args.dryrun, force_overwrite=args.force_overwrite)
