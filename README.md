# NCBI C++ Toolkit package recipe

1. [Quick start.](#recipe_Start)
2. What is Conan and why you might need it?
3. Preparing work environment.
4. Building your project.
5. Define build options.
6. Supported 3rd party packages.
7. There are few things to note.
8. Data serialization support.

<a name="recipe_Start"></a>
## Quick start.

Clone this repository and export the recipe into the local Conan cache:

    git clone https://github.com/ncbi/ncbi-cxx-toolkit-conan
    cd ncbi-cxx-toolkit-conan
    conan export .

Reference the package in conanfile.txt of your project:

    [requires]
    ncbi-cxx-toolkit-public/0.3.0
    [options]
    ncbi-cxx-toolkit-public:targets=xncbi

Install the requirements and configure the projects

    conan install . --build missing
    cmake .

## What is Conan and why you might need it?

[Conan](https://docs.conan.io/en/latest/) is an Open Source package manager for C and C++ development, 
allowing development teams to easily and efficiently
manage their packages and dependencies across platforms and build systems. Conan can manage any number of different 
binaries for different build configurations, including different architectures, compilers, compiler versions, runtimes, 
C++ standard library, etc. When binaries are not available for one configuration, they can be built from sources on-demand.

When using NCBI C++ Toolkit at NCBI, there is good chance you do not need Conan. 
Different versions of Toolkit libraries and applications are readily available, as well as a long list of third party libraries. 
Still, there is always a chance you need something special. Conan might be the answer.

Using NCBI C++ Toolkit outside of NCBI is much more tricky. You need to download and build certain third party libraries, 
then the Toolkit itself. It is not always clear what exactly is required. Conan's help might be very useful in this scenario.


## Preparing work environment.

First, you need Conan. For instructions of how to install Conan, please refer to [Conan's documentation](https://docs.conan.io/en/latest/installation.html).

Next, you need to add conan-center remote repository:

    $ conan remote add conan-center https://center.conan.io
    $ conan remote list
    conan-center: https://center.conan.io [Verify SSL: True]



Make sure *cmake* is found in *PATH*. On MacOS and Windows this might require correcting the *PATH* environment variable.
Finally. NCBI C++ Toolkit is large. Building it locally requires a lot of disk space. By default, Conan's local cache is located 
in user home directory, which, most likely does not have enough space. To place Conan's cache into another location, 
you should define [CONAN_USER_HOME](https://docs.conan.io/en/latest/reference/env_vars.html) environment variable.


## Building your project.

Let us build [blast_demo](https://github.com/ncbi/ncbi-cxx-toolkit-public/blob/master/src/sample/app/blast/CMakeLists.blast_demo.app.txt) sample application. It requires one source file and some unknown number of the Toolkit libraries. 
What we know for sure is that we need *blastinput* library.

Copy *blast_demo.cpp* into a local directory. Next to it, create *conanfile.txt*:

    [requires]
    ncbi-cxx-toolkit-public/0.3.0
    [options]
    ncbi-cxx-toolkit-public:targets=blastinput
    [generators]
    cmake


and *CMakeLists.txt*:

    cmake_minimum_required(VERSION 3.7)
    project(conanapp CXX)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()
    add_executable(blast_demo blast_demo.cpp)
    target_link_libraries(blast_demo ${CONAN_LIBS})


Create build directory and install build requirements:

    mkdir build
    cd build
    conan install .. --build missing


Configure and build:

    cmake ..
    make



## Define build options.

NCBI C++ Toolkit libraries can be built as either shared or static ones. The same applies to external packages. 
You can request desired options in conanfile.txt. For example, the following instructs Conan to use NCBI C++ Toolkit 
shared libraries and use static libraries of external packages:

    [requires]
    ncbi-cxx-toolkit-public/0.3.0
    [options]
    ncbi-cxx-toolkit-public:targets=blastinput
    ncbi-cxx-toolkit-public:shared=True
    ncbi-cxx-toolkit-public:sharedDeps=False
    [generators]
    cmake


To switch between Debug and Release build types, you can use command line when installing Conan dependencies:

    conan install .. -s build_type=Debug --build missing
    cmake .. -DCMAKE_BUILD_TYPE=Debug


## Supported 3rd party packages.

The Toolkit uses a number of 3-rd party packages. The following is the list of packages supported by *ncbi-cxx-toolkit-public* 
Conan recipe (as of July 2021):

    BerkeleyDB, BZ2, CASSANDRA, EXSLT, GIF, GRPC, JPEG, LMDB, LZO, MySQL, NGHTTP2,
    PCRE, PNG, PROTOBUF, SQLITE3, TIFF, XML, XSLT, UV, Z


## There are few things to note.

The whole Toolkit contains about 250 libraries. You probably do not need all of them. That is why it is highly 
recommended that you specify what exactly you need in options section of conanfile.txt. It is possible to list 
several libraries here using semicolon separator:

    [options]
    ncbi-cxx-toolkit-public:targets=blastinput;xncbi;xser


You do not need to know all the dependencies. They will be collected automatically. For example, in case of *blastinput* 
library Conan will build and use 58 ones.

*CONAN_LIBS* macro collects all libraries into one blob. That is, if you do not specify *ncbi-cxx-toolkit-public:targets*, 
all 250 toolkit libraries, as well as all external ones will be in that blob. This might work. The linker will figure out 
what exactly it needs, but it definitely will be overwhelmed. Also, it takes more time to build libraries which you do not really need.

Note that using *CONAN_LIBS* is not a requirement. It is perfectly possible to reference *blastinput* directly. Change your CMakeLists.txt to look as follows:

    cmake_minimum_required(VERSION 3.7)
    project(conanapp CXX)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()
    add_executable(blast_demo blast_demo.cpp)
    target_link_libraries(blast_demo blastinput)

This approach is better in a sense that you can drop *ncbi-cxx-toolkit-public:targets* setting in conanfile.txt configuration file. Yes, *CONAN_LIBS* macro will include all the libraries, but you do not use it any longer. Also, once the Toolkit installation contains all libraries, it is possible to reuse it in different projects. When you do not know exactly what does your project require, you can add libraries into the *target_link_libraries* command one by one.


## Data serialization support.

### Datatool.

The Toolkit contains [datatool](https://ncbi.github.io/cxx-toolkit/pages/ch_app.html#ch_app.datatool) application, which can generate C++ data storage classes from ASN.1, DTD, XML schema or JSON schema specification. These classes can then be used to [read and write data](https://ncbi.github.io/cxx-toolkit/pages/ch_ser) in ASN.1, XML or JSON format.
To add code generation into a project, use *NCBI_generate_cpp* command. For example:

    cmake_minimum_required(VERSION 3.7)
    project(conanapp CXX)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()
    NCBI_generate_cpp(GEN_SOURCES GEN_HEADRS sample.asn)
    add_executable(asn_demo asn_demo.cpp ${GEN_SOURCES} ${GEN_HEADRS})
    target_link_libraries(asn_demo xser)

First two parameters to *NCBI_generate_cpp* receive a list of generated files - sources and headers. After that goes one or more data specifications. Files will be generated during the build in the directory where the specification is.

### Protocol buffers and gRPC.

[gRPC](https://grpc.io) is an open source high performance Remote Procedure Call framework. By default, gRPC uses [Protocol Buffers](https://developers.google.com/protocol-buffers/docs/overview), Google’s open source mechanism for serializing structured data.

First, make sure your project contains proper requirements. For example, conanfile.txt can request *protobuf* and *grpc*:

    [requires]
    ncbi-cxx-toolkit-public/0.3.0
    protobuf/3.17.1
    grpc/1.38.0

Next, you can use their own mechanisms, or the same NCBI function *NCBI_generate_cpp*:

    cmake_minimum_required(VERSION 3.7)
    project(conanapp CXX)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()
    NCBI_generate_cpp(GEN_SOURCES GEN_HEADRS sample.proto)
    add_library(grpc_demo grpc_demo.cpp ${GEN_SOURCES} ${GEN_HEADRS})
    
By default, *NCBI_generate_cpp* generates *protocol buffers* files only. To instruct it to generate gRPC ones as well, use *GEN_OPTIONS* flags, like this:

    NCBI_generate_cpp(GEN_SOURCES GEN_HEADRS sample.proto GEN_OPTIONS grpc)

