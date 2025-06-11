import os
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.references.reference_results import ReferenceResults


class PossibleFilenames:
    #
    # this class gets matches without filtering them. if we use a
    # results after this update without any further processing it
    # is the most general set of results and very likely wrong.
    #
    @classmethod
    def update(cls, results: ReferenceResults, *, exact: bool = False) -> None:
        #
        # if we don't have name_one we should already have all arrivals loaded.
        # in that case those are the possibles.
        #
        if results.ref.name_one is None:
            return
        ref = results.ref
        csvpaths = results.csvpaths
        #
        # this is an exact match, or, if no exact match, a prefix match. it takes:
        #   > :first|:last|:all
        #   > a prefix date in the ref.name_three position (i.e. $n.files.x.date
        #
        looking_for = ref.name_one
        name = ref.root_major
        base = csvpaths.config.get(section="inputs", name="files")
        starting = os.path.join(base, name)
        #
        #
        #
        e = os.path.join(starting, looking_for)
        if exact is True:
            nos = Nos(e)
            #
            # need to check dir for being 1) exact match and 2) the direct parent
            # of actual data files. we can assume that any files we find means we're
            # in the right place. we return all the files.
            #
            if nos.dir_exists():
                files = nos.listdir(files_only=True, recurse=False)
                for file in files:
                    results.files.append(os.path.join(nos.path, file))
            return
        else:
            lf = os.path.join(starting, looking_for)
            lf = pathu.resep(lf)
            nos = Nos(starting)
            lst = nos.listdir(files_only=True, recurse=True)
            for file in lst:
                if file.find("manifest.json") > -1:
                    continue
                #
                # if we have a prefix match and there are no directories we are at the
                # physical file level. every file should be a delimited data file named
                # by its sha256 fingerprint + extension.
                #
                match = file.startswith(lf)
                if match:
                    results.files.append(file)
                    continue
                #
                # check if we have an extension that needs dot to become underscore because
                # dots don't work for references.
                #
                # we don't want to keep the _ in the path going forward tho. this should be
                # the only tool that cares. and the mismatch it causes with the mani is a pia
                #
                i = file.find(".")
                j = i + 1
                filetemp = f"{file[0:i]}_{file[j:]}"
                match = filetemp.startswith(lf)
                if match:
                    results.files.append(file)
