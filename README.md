# NCBI C++ Toolkit package recipe

1. [What is Conan and why you might need it?](#recipe_Conan)
2. [Preparing work environment.](#recipe_Env)
3. [Building your project.](#recipe_Build)
4. [Define build options.](#recipe_Options)
5. [Semantic components of the Toolkit.](#recipe_Components)
6. [Supported 3rd party packages.](#recipe_Other)
7. [Data serialization support.](#recipe_Serial)
8. [NCBIptb build process management.](#recipe_NCBIptb)


<a name="recipe_Conan"></a>
## What is Conan and why you might need it?

[Conan](https://docs.conan.io/2/) is an Open Source package manager for C and C++ development, 
allowing development teams to easily and efficiently
manage their packages and dependencies across platforms and build systems. Conan can manage any number of different 
binaries for different build configurations, including different architectures, compilers, compiler versions, runtimes, 
C++ standard library, etc. When binaries are not available for one configuration, they can be built from sources on-demand.

When using NCBI C++ Toolkit at NCBI, there is good chance you do not need Conan. 
Different versions of Toolkit libraries and applications are readily available, as well as a long list of third party libraries. 
Still, there is always a chance you need something special. Conan might be the answer.

Using NCBI C++ Toolkit outside of NCBI is much more tricky. You need to download and build certain third party libraries, 
then the Toolkit itself. It is not always clear what exactly is required. Conan's help might be very useful in this scenario.


<a name="recipe_Env"></a>
## Preparing work environment.

First, you need Conan (and, to install Conan, you need Python). For instructions of how to install Conan, please refer to [Conan's documentation](https://docs.conan.io/2/installation.html).

On February 22, 2023 Conan 2.0 was released. It is a major upgrade, which features new public API, new build system integration and new graph model to represent relations between packages. What is important is that it is not always backward compatible with Conan 1.X.

The Toolkit recipe is fully compatible both with Conan 1.X and 2.X. We strongly recommend using Conan2.

Install Conan:

    pip install conan

or, to install a specific version:

    pip install conan==2.13.0

If needed, upgrade Conan installation:

    pip install conan --upgrade

Next, check the list of Conan repositories and add *center.conan.io*:

    $ conan remote add conancenter https://center2.conan.io
    $ conan remote list
    conancenter: https://center2.conan.io [Verify SSL: True]

Make sure *cmake* is found in *PATH*. On MacOS and Windows this might require correcting the *PATH* environment variable.
Finally. NCBI C++ Toolkit is large. Building it locally requires a lot of disk space. By default, Conan's local cache is located 
in user home directory, which, most likely does not have enough space. To place Conan's cache into another location, 
you should define [CONAN_HOME](https://docs.conan.io/2/reference/environment.html) environment variable.

Check the list of Conan [profiles](https://docs.conan.io/2/reference/commands/profile.html). Create *default* one:

    conan profile list
    conan profile detect
    conan profile show

Profiles can only be edited manually. Find profile location:

    conan profile path default

Clone this repository and export the recipe into the local Conan cache:

    git clone https://github.com/ncbi/ncbi-cxx-toolkit-conan.git
    cd ncbi-cxx-toolkit-conan
    conan export . --version 29.0.0

Please check *conandata.yml* file in this repository for the list of existing NCBI C++ Toolkit versions.


<a name="recipe_Build"></a>
## Building your project.

Let us build [blast_demo](https://github.com/ncbi/ncbi-cxx-toolkit-public/blob/master/src/sample/app/blast/CMakeLists.blast_demo.app.txt) sample application.
It requires one source file and some unknown number of the Toolkit libraries. 
What we know for sure is that we need *blastinput* library.

Copy *blast_demo.cpp* into a local directory. Next to it, create [*conanfile.py*](https://docs.conan.io/2/reference/conanfile.html):

    from conan import ConanFile
    from conan.tools.cmake import cmake_layout
    class NCBIapp(ConanFile):
        settings = "os", "compiler", "build_type", "arch"
        generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
        def requirements(self):
            self.requires("ncbi-cxx-toolkit-public/[>=29]")
        def configure(self):
            self.options["ncbi-cxx-toolkit-public/*"].with_targets = "blastinput"
        def layout(self):
            cmake_layout(self, src_folder=".")

It is also possible to use [*conanfile.txt*](https://docs.conan.io/2/reference/conanfile_txt.html) - a simplified version of *conanfile.py*:

    [requires]
    ncbi-cxx-toolkit-public/29.0.0
    [options]
    ncbi-cxx-toolkit-public/*:with_targets=blastinput
    [layout]
    cmake_layout
    [generators]
    CMakeDeps
    CMakeToolchain
    VirtualRunEnv

It is difficult to say what is better, but *conanfile.py* definitely provides greater
[flexibility](https://docs.conan.io/2/tutorial/consuming_packages/the_flexibility_of_conanfile_py.html)

Add *CMakeLists.txt*:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    set(ncbitk ncbi-cxx-toolkit-public)
    find_package(${ncbitk} REQUIRED)
    add_executable(blast_demo blast_demo.cpp)
    target_link_libraries(blast_demo ${ncbitk}::${ncbitk})

Install build requirements, in the source directory run

    conan install . --build missing -s build_type=Release

In the source directory, [*CMakeToolchain*](https://docs.conan.io/2/reference/tools/cmake/cmaketoolchain.html)
generates [*CMakeUserPresets.json*](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html).
To list available presets, run

    cmake --list-presets

Run cmake to [configure](https://cmake.org/cmake/help/latest/manual/cmake.1.html#generate-a-project-buildsystem)
the build (*conan-release* is the name of the preset):

    cmake --preset conan-release

and finally, [build](https://cmake.org/cmake/help/latest/manual/cmake.1.html#build-a-project):

    cmake --build --preset conan-release


<a name="recipe_Options"></a>
## Define build options.

NCBI C++ Toolkit libraries can be built as either shared or static ones. The same applies to external packages. 
The recommended way is to specify that in [*conan install*](https://docs.conan.io/2/reference/commands/install.html) command,
or in [Conan profiles](https://docs.conan.io/2/reference/commands/profile.html).
For example, the following instructs Conan to use NCBI C++ Toolkit shared libraries:

    conan install . --build missing -s build_type=Release -o ncbi-cxx-toolkit-public/*:shared=True

To configure Debug build, use *build_type* settings:

    conan install . --build missing -s build_type=Debug
    cmake --preset conan-debug
    cmake --build --preset conan-debug

Normally, defining build flags (compilation and linking) is the responsibility of the user.
Still, it is possible to request the Toolkit to set flags which were used by the Toolkit itself - by
setting *NCBI_PTBCFG_NCBI_BUILD_FLAGS* variable before finding the package:

    set(NCBI_PTBCFG_NCBI_BUILD_FLAGS ON)
    find_package(ncbi-cxx-toolkit-core REQUIRED)

In this case, it is also possible to request additional customizations by defining
[*compilation features*](https://ncbi.github.io/cxx-toolkit/pages/ch_cmconfig#ch_cmconfig._Configure), for example:

    set(NCBI_PTBCFG_NCBI_BUILD_FLAGS ON)
    set(NCBI_PTBCFG_PROJECT_FEATURES MaxDebug)
    find_package(ncbi-cxx-toolkit-core REQUIRED)

Yet another option is using CTest framework provided by the Toolkit. Define *NCBI_PTBCFG_ADDTEST* variable:

    set(NCBI_PTBCFG_ADDTEST ON)
    find_package(ncbi-cxx-toolkit-core REQUIRED)


<a name="recipe_Components"></a>
## Semantic components of the Toolkit.

The whole Toolkit contains about 220 libraries. No application will ever need all of them. There are a couple of options in the Toolkit recipe to limit the number.

*ncbi-cxx-toolkit-public:with_targets* specifies the required libraries. There is no need to list all of them, because the dependent ones will be added automatically.
In the *blast_demo* example above, we request *blastinput* only. The build system then builds and uses 58 libraries.

*ncbi-cxx-toolkit-public:with_components* lists required semantic components. Each component is a set of libraries that share a common or related purpose. 
Components are then defined as CMake [Imported Libraries](https://cmake.org/cmake/help/latest/command/add_library.html#imported-libraries), and it is possible to 
use them in *target_link_libraries* directives. For example, *CMakeLists.txt* for *blast_demo* application could look like this:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    set(ncbitk ncbi-cxx-toolkit-public)
    find_package(${ncbitk} REQUIRED)
    add_executable(blast_demo blast_demo.cpp)
    target_link_libraries(blast_demo ${ncbitk}::blast)

Here is the list of the Toolkit components:

|Component|Libraries|
|-----------|----------|
|algo| cobalt composition_adjustment fastme phytree_format prosplign proteinkmer utrtprof xalgoalignnw xalgoalignsplign xalgoalignutil xalgoblastdbindex xalgocontig_assembly xalgodustmask xalgognomon xalgophytree xalgosegmask xalgoseq xalgoseqqa xalgotext xalgowinmask xblast xblastformat xid_mapper xprimer|
|algo-ms| omssa pepXML xomssa|
|algo-structure| xbma_refiner xcd_utils xstruct_dp xstruct_thread xstruct_util|
|align-format| align_format xalntool|
|bamread| bamread|
|blast| blast_sra_input blastinput gumbelparams igblast vdb2blast xalgoblastdbindex_search xmergetree xngalign|
|core| sequtil tables xalgovmerge xcompress xconnect xconnext xconnserv xdiff xncbi xqueryparse xregexp xser xthrserv xutil xxconnect2 zcf|
|dbapi| ct_ftds14 dbapi dbapi_driver dbapi_util_blobstore ncbi_xdbapi_ftds ncbi_xdbapi_ftds14 sdbapi tds_ftds14|
|eutils| egquery ehistory einfo elink epost esearch espell esummary eutils eutils_client linkout uilist|
|grpc| grpc_integration|
|image| ximage|
|loader-asncache| asn_cache bdb ncbi_xcache_bdb ncbi_xloader_asn_cache|
|loader-bam| ncbi_xloader_bam|
|loader-blastdb| ncbi_xloader_blastdb ncbi_xloader_blastdb_rmt|
|loader-cdd| cdd_access ncbi_xloader_cdd|
|loader-genbank| eMyNCBI_result ncbi_xloader_genbank ncbi_xreader ncbi_xreader_cache ncbi_xreader_gicache ncbi_xreader_id1 ncbi_xreader_id2 ncbi_xreader_pubseqos ncbi_xreader_pubseqos2 xobjsimple|
|loader-lds2| lds2 ncbi_xloader_lds2|
|loader-snp| dbsnp_ptis ncbi_xloader_snp|
|loader-sra| ncbi_xloader_csra ncbi_xloader_sra|
|loader-wgs| ncbi_xloader_vdbgraph ncbi_xloader_wgs|
|loaders| data_loaders_util ncbi_xloader_patcher xflatfile|
|objects| access biblio biotree blastdb blastxml blastxml2 cdd cn3d docsum efetch entrez2 entrez2cli entrezgene featdef gbproj gbseq gencoll_client generalasn genesbyloc genome_collection homologene insdseq local_taxon macro medlars medline mim mmdb ncbimime objcoords objprt pcassay pcassay2 pcsubstance proj pub pubmed remap remapcli scoremat searchbyrsid seq seqcode seqedit seqset seqtest submit taxon1 taxon3 tinyseq trackmgr trackmgrcli variation xnetblast xnetblastcli|
|psg-client| psg_client psg_protobuf|
|seqext| blast_services blastdb_format id1 id1cli id2 id2_split id2cli seqdb seqmasks_io seqsplit snputil uudutil valerr valid variation_utils writedb xalnmgr xcleanupxdiscrepancy xformat xhugeasn xlogging xobjedit xobjimport xobjmanip xobjmgr xobjread xobjreadex xobjutil xobjwrite xunittestutil xvalidate|
|sqlitewrapp| sqlitewrapp|
|sraread| sraread srareadx|
|xmlwrapp| xmlreaders xmlwrapp|
|web| ncbi_web xcgi xcgi_redirect xhtml xsoap xsoap_server|


<a name="recipe_Other"></a>
## Supported 3rd party packages.

The Toolkit uses a number of 3-rd party packages. In the Toolkit code they are known by their aliases.
The following is the list of packages supported by *ncbi-cxx-toolkit-public* Conan recipe, as of October 2024:

|Alias|Conan package|
|--------|------------|
|BACKWARD|backward-cpp|
|BerkeleyDB|libdb|
|BZ2|bzip2|
|GIF|giflib|
|GRPC|grpc|
|JPEG|libjpeg|
|LMDB|lmdb|
|LZO|lzo|
|NGHTTP2|libnghttp2|
|PCRE|pcre|
|PNG|libpng|
|PROTOBUF|protobuf|
|SQLITE3|sqlite3|
|TIFF|libtiff|
|UNWIND|libunwind|
|UV|libuv|
|XML|libxml2|
|XSLT|libxslt|
|Z|zlib|
|ZSTD|zstd|


These packages are available for download from [*conancenter*](https://conan.io/center) repository.


<a name="recipe_Serial"></a>
## Data serialization support.

### Datatool.

The Toolkit contains [datatool](https://ncbi.github.io/cxx-toolkit/pages/ch_app.html#ch_app.datatool) application, which can generate C++ data storage classes from ASN.1, DTD, XML schema or JSON schema specification. These classes can then be used to [read and write data](https://ncbi.github.io/cxx-toolkit/pages/ch_ser) in ASN.1, XML or JSON format.
To add code generation into a project, use *NCBI_generate_cpp* command. For example:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    find_package(ncbi-cxx-toolkit-public REQUIRED)
    NCBI_generate_cpp(GEN_SOURCES GEN_HEADERS sample.asn)
    add_executable(asn_demo asn_demo.cpp ${GEN_SOURCES} ${GEN_HEADERS})
    target_link_libraries(asn_demo ncbi-cxx-toolkit-public::core)

First two parameters to *NCBI_generate_cpp* receive lists of generated files - sources and headers. After that goes one or more data specifications. Files will be generated during the build in the directory where the specification is. To put generated files into another directory, use *GEN_SRCOUT* and *GEN_HDROUT* parameters:

    NCBI_generate_cpp(GEN_SOURCES GEN_HEADERS sample.asn GEN_SRCOUT generated_sources GEN_HDROUT generated_headers)


### Protocol buffers and gRPC.

[gRPC](https://grpc.io) is an open source high performance Remote Procedure Call framework. By default, gRPC uses [Protocol Buffers](https://developers.google.com/protocol-buffers/docs/overview), Google’s open source mechanism for serializing structured data.

First, make sure your project contains proper requirements. For example, conanfile.txt may request *protobuf* and *grpc*:

    [requires]
    ncbi-cxx-toolkit-public/29.0.0
    protobuf/5.27.0
    grpc/1.67.1

Next, you can use their own mechanisms, or the same NCBI function *NCBI_generate_cpp*:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    find_package(ncbi-cxx-toolkit-public REQUIRED)
    NCBI_generate_cpp(GEN_SOURCES GEN_HEADRS grpc_test.proto)
    add_library(grpc_sample ${GEN_SOURCES} ${GEN_HEADRS})
    target_link_libraries(grpc_sample ncbi-cxx-toolkit-public::grpc)

By default, *NCBI_generate_cpp* generates *protocol buffers* files only. To instruct it to generate gRPC ones as well, use *GEN_OPTIONS* flags, like this:

    NCBI_generate_cpp(GEN_SOURCES GEN_HEADERS sample.proto GEN_OPTIONS grpc)


<a name="recipe_NCBIptb"></a>
## NCBI build process management.

NCBI C++ Toolkit includes [NCBIptb](https://ncbi.github.io/cxx-toolkit/pages/ch_cmconfig) - CMake wrapper, which can also be used with Conan.

For example, *CMakeLists.txt* for [blast_demo](#recipe_Build) project might as well look like the following:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    find_package(ncbi-cxx-toolkit-public REQUIRED)
    NCBIptb_setup()

    NCBI_begin_app(blast_demo)
      NCBI_sources(blast_demo)
      NCBI_uses_toolkit_libraries(blastinput)
    NCBI_end_app()

Note the use of *NCBIptb_setup()* function. It adds functionalty **required** by *NCBIptb*. It also gives a second chance to request
NCBI-specific build flags, add compilation features and NCBI CTest framework. The function has the following optional arguments:

|Argument|Meaning|
|--------|----------|
|NCBI_BUILD_FLAGS | Set build flags which were used by the Toolkit itself |
|NCBI_CTEST | Enable NCBI CTest framework provided by the Toolkit |
|NCBI_LOCAL_COMPONENTS | In addition to Conan packages, look for locally defined 3rd party packages |
|FEATURES list | List of additional [compilation features](https://ncbi.github.io/cxx-toolkit/pages/ch_cmconfig#ch_cmconfig._Configure) defined by the Toolkit |
|COMPONENTS list | explicitly enable or disable listed [3rd party packages](https://ncbi.github.io/cxx-toolkit/pages/ch_cmconfig#ch_cmconfig._Configure) |

For example:

    NCBIptb_setup( NCBI_BUILD_FLAGS NCBI_CTEST FEATURES MaxDebug Coverage)

*NCBIptb* expects source tree root to have *include* and *src* subdirectories:

    - root
        - include
            - ...
        - src
            - ...

All header files are then expected to be in *include* and its subdirectories; sources - in *src*.

In other words, your root *CMakeLists.txt* should look like this:

    cmake_minimum_required(VERSION 3.16)
    project(conanapp)
    find_package(ncbi-cxx-toolkit-public REQUIRED)
    NCBIptb_setup()
    NCBI_add_subdirectory(src)

The *blast_demo* example above will also work, of course. But as long as you add more and more projects, it is practically imperative that you adopt the standard NCBIptb source tree structure.

In case of data serialization projects, you should follow the standard *NCBIptb* practice - use *NCBI_dataspecs* function call. For example:

    NCBI_begin_lib(asn_sample_lib)
      NCBI_dataspecs(asn_sample_lib.asn)
      NCBI_uses_toolkit_libraries(xser)
    NCBI_end_lib()

