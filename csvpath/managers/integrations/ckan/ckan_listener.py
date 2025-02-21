import os
import json
from tempfile import NamedTemporaryFile
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result import Result
from csvpath.matching.util.runtime_data_collector import RuntimeDataCollector
from .ckan import Ckan, CkanException
from .dataset import Dataset
from .datafile import Datafile


class CkanListener(Listener):

    FILETYPE_MAP = {
        "data": "data.csv",
        "unmatched": "unmatched.csv",
        "errors": "errors.json",
        "vars": "vars.json",
        "meta": "meta.json",
        "manifest": "manifest.json",
        "printouts": "printouts.txt",
    }
    FILETYPES = ["data", "unmatched", "meta", "vars", "errors", "printouts", "manifest"]

    def __init__(self, config=None, csvpaths=None):
        #
        # we're unlikely to get either of these because
        # we're loading dynamically. we'll get them after
        # init.
        #
        super().__init__(config=config)
        self._csvpaths = None

    def manifest(self, metadata: Metadata) -> dict[str, ...]:
        path = metadata.manifest_path
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @property
    def csvpaths(self):
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    def metadata_update(self, mdata: Metadata) -> None:
        #
        # CKAN is mainly interested in the output file and/or metadata.
        # we can assume that we don't need to react to file, paths,
        # and run events.
        #
        # CKAN cares about individual csvpath instances within the
        # named-paths group. however, it needs to be able to react to
        # a csvpath based on the results of all the other csvpaths in
        # the group. that means we need to work from the results event
        # rather than the result events. using the results event is
        # easy because it is at the right point in time, already
        # collects the summary good/bad indicators, and we have all
        # the data we need to run through the individual csvpaths to
        # look for CKAN work.
        #
        if isinstance(mdata, ResultsMetadata):
            return self._send_result_files(mdata)

    def _send_result_files(self, mdata: Metadata) -> None:
        mani = self.manifest(mdata)
        if "time_completed" not in mani or mani["time_completed"] is None:
            #
            # the run has started but not completed
            #
            return
        #
        # if for some reason we don't get back our correct results -- the most recent
        # results available -- we can use results_manager.get_named_results_for_run()
        # to find the right set
        #
        results = self.csvpaths.results_manager.get_named_results(
            mdata.named_paths_name
        )
        if results is None:
            raise CkanException(f"Results cannot be none for {mdata.named_paths_name}")
        if len(results) == 0:
            raise CkanException(f"Results cannot be 0 for {mdata.named_paths_name}")
        if not mdata.run_home.endswith(results[0].run_dir):
            raise CkanException(
                f"Results of {mdata.named_paths_name} from wrong run dir: {results[0].run_dir}"
            )
        #
        # we're good. we iterate all and for each we check if the instance requires
        # all other instances to be valid,complete,no-errors. if so, we iterate for
        # that. if all is good we follow the metadata instructions.
        #
        for result in results:
            self._handle_result(results, result, mdata)

    def _handle_result(
        self, results: list[Result], result: Result, mdata: Metadata
    ) -> None:
        #
        # give the Dataset object a chance to find any new metadata
        # we want to apply to the dataset in CKAN. we may need to
        # pull the CKAN package to see what's already there, or not,
        # or maybe leave that to the CKAN client to adjudicate, if
        # we're ok with overwriting fields and don't lose existing
        # metadata if we don't present it again during the update?
        #
        """
        Metadata directives for CKAN:
          - ckan-publish: always | on-valid | on-all-valid | never
          - ckan-group: use-archive | use-named-results | some-literal
          - ckan-dataset-name: use-instance | use-named-results | var-value:name | a literal
          - ckan-dataset-title: a-metadata-field-name | var-value:name
          - ckan-visibility: private
          - ckan-tags: static-tag1-n | instance-identity | instance-home | var-value:name
          - ckan-show-fields: a, b, c, d....
          - ckan-send: all, printouts, data, metadata, unmatched, vars, errors, manifest
          - ckan-printouts-title: Background
          - ckan-data-title: Orders
          - ckan-unmatched-title: Orders
          - ckan-vars-title: Orders
          - ckan-meta-title: Orders
          - ckan-errors-title: Orders
          - ckan-split-printouts: (no-)split
        """
        pub = self._publish(results=results, result=result)
        if not pub:
            return
        #
        # get manifest
        #
        mani = self.manifest(mdata)
        dataset = Dataset(listener=self, manifest=mani, metadata=mdata)
        #
        # look in metadata for instructions as to if we use a group, and if so,
        # how it is named.
        #
        self._set_group(dataset=dataset, result=result, mani=mani, mdata=mdata)
        #
        # look in metadata for instructions on how to map to the dataset; what name to use, etc.
        #
        self._set_dataset_name(dataset=dataset, result=result, mani=mani, mdata=mdata)
        #
        # find a title if any
        #
        self._set_dataset_title(dataset=dataset, result=result)
        #
        # find a visibility if any
        #
        self._set_visibility(dataset=dataset, result=result)
        #
        # tags to label the dataset with
        #
        self._set_tags(dataset=dataset, result=result, mdata=mdata)
        #
        # metadata fields to display in the dataset
        #
        self._set_metadata_fields(dataset=dataset, result=result)
        #
        # create the dataset before we load the files, or update it if existing
        #
        ckan = Ckan(config=self.config, manifest=mani, csvpaths=self.csvpaths)
        ckan.create_or_update_dataset(dataset)
        #
        # send any files requested. one or more makes sense, but there is no requirement to send any.
        #
        self._send_files(result=result, mani=mani, mdata=mdata, dataset_id=dataset.name)

    def _publish(self, *, results, result) -> bool:
        pub = result.csvpath.metadata.get("ckan-publish")
        ret = None
        if pub is None:
            ret = False
        else:
            pub = pub.strip().lower()
        if pub == "never":
            ret = False
        elif pub == "always":
            ret = True
        elif pub == "on-valid":
            ret = result.csvpath.is_valid
        elif pub == "on-all-valid":
            ret = True
            for r in results:
                if not r.is_valid:
                    ret = False
                    break
        return ret

    def _send_files(
        self, *, result: Result, mani: dict, mdata: Metadata, dataset_id: str
    ) -> None:
        filesstr = result.csvpath.metadata.get("ckan-send")
        files = []
        if filesstr is not None:
            if filesstr.strip() == "all":
                files = CkanListener.FILETYPES[:]
            else:
                fs = filesstr.split(",")
                for f in fs:
                    f = f.strip().lower()
                    if f not in CkanListener.FILETYPES:
                        raise ValueError(
                            f"Incorrect file identifier: {f}. Must be in {CkanListener.FILETYPES}."
                        )
                    files.append(f)
        for file in files:
            path = os.path.join(mani["run_home"], result.identity_or_index)
            path = os.path.join(path, CkanListener.FILETYPE_MAP[file])
            #
            # move printouts out
            #
            if file == "printouts":
                split = result.csvpath.metadata.get("ckan-split-printouts")
                if split and split.strip().lower() == "split":
                    if os.path.exists(path):
                        printouts = ""
                        with open(path, "r", encoding="utf-8") as file:
                            printouts = file.read()
                        printouts = printouts.split("---- PRINTOUT:")
                        for p in printouts:
                            self._send_a_printout(
                                p=p,
                                result=result,
                                mani=mani,
                                mdata=mdata,
                                dataset_id=dataset_id,
                            )
            else:
                datafile = Datafile(
                    listener=self,
                    result=result,
                    manifest=mani,
                    metadata=mdata,
                    filetype=file,
                    path=path,
                )
                datafile.dataset_id = dataset_id
                title = result.csvpath.metadata.get(f"ckan-{file}-title")
                if title is not None:
                    datafile.name = title
                ckan = Ckan(config=self.config, manifest=mani, csvpaths=self.csvpaths)
                ckan.upload_datafile(datafile)

    def _send_a_printout(
        self, *, p: str, result: Result, mani: dict, mdata: Metadata, dataset_id: str
    ) -> None:
        i = p.find("\n")
        name = p[0:i]
        name = name.strip()
        if name == "default":
            name = result.csvpath.metadata.get("ckan-printouts-title")
            if name is None:
                name = "Default printer"
        body = p[i + 1 :]
        body = body.strip()
        if body == "":
            return
        with NamedTemporaryFile() as file:
            file.write(body.encode("utf-8"))
            file.close()
            datafile = Datafile(
                listener=self,
                result=result,
                manifest=mani,
                metadata=mdata,
                filetype="printouts",
                path=file.name,
            )
            datafile.dataset_id = dataset_id
            datafile.name = name
            datafile.mime_type = "text/plain"
            ckan = Ckan(config=self.config, manifest=mani, csvpaths=self.csvpaths)
            ckan.upload_datafile(datafile)

    def _set_visibility(self, dataset: Dataset, result: Result) -> None:
        visibility = result.csvpath.metadata.get("ckan-visibility")
        if visibility and visibility.strip().lower() == "public":  # not private
            dataset.visible = False

    def _set_group(
        self, *, dataset: Dataset, result: Result, mani: dict, mdata: Metadata
    ):
        g = self._create_group_if(
            dataset=dataset, result=result, mani=mani, mdata=mdata
        )
        dataset.group = g

    def _create_group_if(
        self, *, dataset: Dataset, result: Result, mani: dict, mdata: Metadata
    ) -> str:
        group, title = self._get_group_name(result, mdata)
        if group is None:
            return
        ckan = Ckan(config=self.config, manifest=mani, csvpaths=self.csvpaths)
        group = ckan.create_group_if(name=group, title=title)
        return group

    def _get_group_name(self, result: Result, mdata: Metadata) -> str:
        group = result.csvpath.metadata.get("ckan-group")
        title = group
        if group is not None:
            group = group.strip().lower()
            if group == "use-archive":
                group = mdata.archive_name
                title = group
            elif group == "use-named-results":
                group = mdata.named_results_name
                title = group
            group = group.strip().lower()
        return (group, title)

    def _set_dataset_name(
        self, *, dataset: Dataset, result: Result, mani: dict, mdata: Metadata
    ) -> None:
        slug = result.csvpath.metadata.get("ckan-dataset-name")
        lslug = None
        if slug is not None:
            slug = slug.strip()
            lslug = slug.lower()
        if lslug == "use-instance":
            dataset.name = result.csvpath.identity
        elif lslug == "use-named-results":
            dataset.name = mdata.named_results_name
        elif lslug is not None and lslug.startswith("var-value:"):
            v = lslug[10:]
            val = result.csvpath.variables.get(v)
            if val is not None:
                dataset.name = val if val else v
        elif slug is not None:
            dataset.name = slug
        else:
            dataset.name = mdata.named_results_name

    def _set_dataset_title(self, *, dataset: Dataset, result: Result) -> None:
        title = result.csvpath.metadata.get("ckan-dataset-title")
        if title is not None:
            if title.startswith("var-value:"):
                v = title[10:]
                v = result.csvpath.variables.get(v)
                if v is not None:
                    title = v
            dataset.title = title

    def _set_tags(self, *, dataset: Dataset, result: Result, mdata: Metadata) -> None:
        tagsstr = result.csvpath.metadata.get("ckan-tags")
        tags = []
        if tagsstr is not None:
            ts = tagsstr.split(",")
            for t in ts:
                t = t.strip()
                if t == "instance-identity":
                    tags.append({"name": f"{result.csvpath.identity}"})
                elif t == "instance-home":
                    h = mdata.run_home
                    if h is not None:
                        tags.append({"name": f"{h}"})
                elif t.startswith("var-value:"):
                    v = t[10:]
                    v = result.csvpath.variables.get(v)
                    if v is not None:
                        tags.append({"name": f"{v}"})
                else:
                    tags.append({"name": f"{t}"})
        if len(tags) > 0:
            dataset.tags = tags

    def _set_metadata_fields(self, *, dataset: Dataset, result: Result) -> None:
        fieldsstr = result.csvpath.metadata.get("ckan-show-fields")
        fields = []
        if fieldsstr is not None:
            fs = fieldsstr.split(",")
            runt = None
            for f in fs:
                f = f.strip()
                v = result.csvpath.metadata.get(f)
                if v is None and f.startswith("var-value:"):
                    f = f[10:]
                    v = result.csvpath.variables.get(f)
                if v is None:
                    if runt is None:
                        runt = {}
                        RuntimeDataCollector.collect(result.csvpath, runt, local=True)
                    v = runt.get(f)
                if v is not None:
                    fields.append({"key": f"{f}", "value": f"{v}"})
        if len(fields) > 0:
            dataset.fields = fields
