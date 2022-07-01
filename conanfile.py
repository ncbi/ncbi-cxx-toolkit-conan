from conans import ConanFile, CMake, tools
from conans.errors import ConanException
from conans.errors import ConanInvalidConfiguration
import os
import shutil
import subprocess
import tempfile
import sys
import stat

def _remove_readonly(fn, path, excinfo):
    try:
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    except Exception as exc:
        print("Skipped: ", path, " because ", exc)

class NcbiCxxToolkit(ConanFile):
    name = "ncbi-cxx-toolkit-public"
    license = "CC0-1.0"
    homepage = "https://ncbi.github.io/cxx-toolkit"
    url = "https://github.com/ncbi/ncbi-cxx-toolkit-conan.git"
    description = "NCBI C++ Toolkit -- a cross-platform application framework and a collection of libraries for working with biological data."
    topics = ("ncbi", "biotechnology", "bioinformatics", "genbank", "gene",
              "genome", "genetic", "sequence", "alignment", "blast",
              "biological", "toolkit", "c++")
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package"
    short_paths = False

    tk_tmp_tree = ""
    tk_src_tree = ""
    all_NCBI_requires = {}

    options = {
        "shared":     [True, False],
        "fPIC":       [True, False],
        "with_projects": "ANY",
        "with_targets":  "ANY",
        "with_tags":     "ANY",
        "with_local": [True, False]
    }
    default_options = {
        "shared":     False,
        "fPIC":       True,
        "with_projects":  "",
        "with_targets":   "",
        "with_tags":      "",
        "with_local": False
    }
    NCBI_to_Conan_requires = {
        "BACKWARD":     "backward-cpp/1.6",
        "UNWIND":       "libunwind/1.6.2",
        "BerkeleyDB":   "libdb/5.3.28",
        "Boost":        "boost/1.79.0",
        "BZ2":          "bzip2/1.0.8",
        "CASSANDRA":    "cassandra-cpp-driver/2.15.3",
        "GIF":          "giflib/5.2.1",
        "GRPC":         "grpc/1.43.2",
        "JPEG":         "libjpeg/9d",
        "LMDB":         "lmdb/0.9.29",
        "LZO":          "lzo/2.10",
        "MySQL":        "libmysqlclient/8.0.25",
        "NGHTTP2":      "libnghttp2/1.47.0",
        "PCRE":         "pcre/8.45",
        "PNG":          "libpng/1.6.37",
        "PROTOBUF":     "protobuf/3.20.0",
        "SQLITE3":      "sqlite3/3.38.1",
        "TIFF":         "libtiff/4.3.0",
        "XML":          "libxml2/2.9.13",
        "XSLT":         "libxslt/1.1.34",
        "UV":           "libuv/1.44.1",
        "Z":            "zlib/1.2.12",

        "OpenSSL":      "openssl/1.1.1n"
    }
    Conan_package_options = {
        "libnghttp2": {
            "with_app": False,
            "with_hpack": False
        },
        "grpc": {
            "cpp_plugin": True,
            "csharp_plugin": False,
            "node_plugin": False,
            "objective_c_plugin": False,
            "php_plugin": False,
            "python_plugin": False,
            "ruby_plugin": False
        }
    }

#----------------------------------------------------------------------------
    def set_version(self):
        if self.version == None:
            self.version = "26.0.0"

    def __del__(self):
        if os.path.isdir(self.tk_tmp_tree):
            print("Just a moment...")
            self._remove_tmp_tree(self.tk_tmp_tree)

    def _remove_tmp_tree(self, path):
        if os.path.isdir(path):
            os.chdir(os.path.join(self.tk_tmp_tree, ".."))
            try:
                shutil.rmtree(path, onerror=_remove_readonly)
            except:
                print("Cannot remove directory: ", path)
                print("Please remove it manually")

#----------------------------------------------------------------------------
    def _get_RequiresMapKeys(self):
        return self.NCBI_to_Conan_requires.keys()

#----------------------------------------------------------------------------
    def _translate_ReqKey(self, key):
        if key in self.NCBI_to_Conan_requires.keys():
#ATTENTION
            if (key == "BACKWARD" or key == "UNWIND") and (self.settings.os == "Windows" or self.settings.os == "Macos"):
                return None
            if key == "BerkeleyDB" and self.settings.os == "Windows":
                return None
            if key == "CASSANDRA" and (self.settings.os == "Windows" or self.settings.os == "Macos"):
                return None
            return self.NCBI_to_Conan_requires[key]
        return None

#----------------------------------------------------------------------------
    @property
    def _source_subfolder(self):
        return "src"

    @property
    def _build_subfolder(self):
#ATTENTION: v26 does not support "build_subfolder"
        return "b" if tools.Version(self.version).major != "26" else "."

    def _get_Source(self):
        self.tk_tmp_tree = tempfile.mkdtemp(dir=os.getcwd())
        src = os.path.normpath(os.path.join(self.recipe_folder, "..", "source", self._source_subfolder))
        src_found = False;
        if os.path.isdir(src):
            self.tk_src_tree = src
            src_found = True;
        else:
            print("getting Toolkit sources...")
            tk_url = self.conan_data["sources"][self.version]["url"] if "url" in self.conan_data["sources"][self.version].keys() else ""
            tk_git = self.conan_data["sources"][self.version]["git"] if "git" in self.conan_data["sources"][self.version].keys() else ""
            tk_branch = self.conan_data["sources"][self.version]["branch"] if "branch" in self.conan_data["sources"][self.version].keys() else "master"
            tk_svn = self.conan_data["sources"][self.version]["svn"] if "svn" in self.conan_data["sources"][self.version].keys() else ""

            if tk_url != "":
                print("from url: " + tk_url)
                curdir = os.getcwd()
                os.chdir(self.tk_tmp_tree)
                tools.get(tk_url, strip_root = True)
                os.chdir(curdir)
                src_found = True;

            if not src_found and tk_git != "":
                print("from git: " + tk_git + "/" + tk_branch)
                try:
                    git = tools.Git(self.tk_tmp_tree)
                    git.clone(tk_git, branch = tk_branch, args = "--single-branch", shallow = True)
                    src_found = True;
                except Exception:
                    print("git failed")

            if not src_found and tk_svn != "":
                print("from svn: " + tk_svn)
                try:
                    svn = tools.SVN(self.tk_tmp_tree)
                    svn.checkout(tk_svn)
                    src_found = True;
                except Exception:
                    print("svn failed")

            if not src_found:
                raise ConanException("Failed to find the Toolkit sources")
            self.tk_src_tree = os.path.join(self.tk_tmp_tree, self._source_subfolder)

#----------------------------------------------------------------------------
    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["NCBI_PTBCFG_PACKAGING"] = "TRUE"
        if self.options.shared:
            cmake.definitions["NCBI_PTBCFG_ALLOW_COMPOSITE"] = "TRUE"
        cmake.definitions["NCBI_PTBCFG_PROJECT_LIST"] = str(self.options.with_projects) + ";-app/netcache"
        if self.options.with_targets != "":
            cmake.definitions["NCBI_PTBCFG_PROJECT_TARGETS"] = self.options.with_targets
        if self.options.with_tags != "":
            cmake.definitions["NCBI_PTBCFG_PROJECT_TAGS"] = self.options.with_tags
        if self.options.with_local:
            cmake.definitions["NCBI_PTBCFG_USELOCAL"] = "TRUE"
        if self.settings.compiler == "Visual Studio":
            cmake.definitions["CMAKE_CONFIGURATION_TYPES"] = self.settings.build_type
        return cmake

#----------------------------------------------------------------------------
    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 14)
        if self.settings.os not in ["Linux", "Macos", "Windows"]:   
            raise ConanInvalidConfiguration("This operating system is not supported")
        if self.settings.compiler == "Visual Studio" and tools.Version(self.settings.compiler.version) < "16":
            raise ConanInvalidConfiguration("This version of Visual Studio is not supported")
        if self.settings.compiler == "Visual Studio" and self.options.shared and "MT" in self.settings.compiler.runtime:
            raise ConanInvalidConfiguration("This configuration is not supported")
        if self.settings.compiler == "gcc" and tools.Version(self.settings.compiler.version) < "7":
            raise ConanInvalidConfiguration("This version of GCC is not supported")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

#----------------------------------------------------------------------------
    def build_requirements(self):
        if hasattr(self, "settings_build") and tools.cross_building(self):
            self.build_requires("{}/{}".format(self.name, self.version))

    def requirements(self):
        if not self.version in self.conan_data["sources"].keys():
            raise ConanException("Invalid Toolkit version requested. Available: " + ' '.join(self.conan_data["sources"].keys()))
        self.output.info("Analyzing requirements. Please wait...")
        curdir = os.getcwd()
        self._get_Source()
        os.chdir(self.tk_tmp_tree)
        shared = "ON" if self.options.shared else "OFF"
        subprocess.run(["cmake", self.tk_src_tree,
            "-DNCBI_PTBCFG_COLLECT_REQUIRES=ON",
            "-DNCBI_PTBCFG_COLLECT_REQUIRES_FILE=req",
            "-DBUILD_SHARED_LIBS='%s'" % shared,
            "-DNCBI_PTBCFG_PROJECT_TARGETS='%s'" % self.options.with_targets,
            "-DNCBI_PTBCFG_PROJECT_LIST='%s'" % self.options.with_projects,
            "-DNCBI_PTBCFG_PROJECT_TAGS='%s'" % self.options.with_tags],
            stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        reqfile = os.path.join(self.tk_src_tree, "..", "req")
        if os.path.isfile(reqfile):
            self.all_NCBI_requires = set(open(reqfile).read().split())
            for req in self.all_NCBI_requires:
                if "Boost" in req:
                    req = "Boost"
                pkg = self._translate_ReqKey(req)
                if pkg is not None:
                    print("Package requires ", pkg)
                    self.requires(pkg)
                    pkg = pkg[:pkg.find("/")]
#ATTENTION
                    if req == "MySQL":
                        self.requires(self._translate_ReqKey("OpenSSL"))
                    if req == "CASSANDRA":
                        self.requires(self._translate_ReqKey("OpenSSL"))
                    if pkg == "libnghttp2":
                        self.options[pkg].with_app = False
                        self.options[pkg].with_hpack = False
                    if pkg == "grpc":
                        self.options[pkg].cpp_plugin = True
                        self.options[pkg].csharp_plugin = False
                        self.options[pkg].node_plugin = False
                        self.options[pkg].objective_c_plugin = False
                        self.options[pkg].php_plugin = False
                        self.options[pkg].python_plugin = False
                        self.options[pkg].ruby_plugin = False
            os.remove(reqfile)
        os.chdir(curdir)

#----------------------------------------------------------------------------
    def source(self):
        if self.tk_tmp_tree == "":
            self._get_Source()
        shutil.move(os.path.join(self.tk_tmp_tree, "include"), ".")
        shutil.move(os.path.join(self.tk_tmp_tree, self._source_subfolder), ".")
        if os.path.isdir(os.path.join(self.tk_tmp_tree, "scripts")):
            shutil.move(os.path.join(self.tk_tmp_tree, "scripts"), ".")
        if os.path.isdir(os.path.join(self.tk_tmp_tree, "doc")):
            shutil.move(os.path.join(self.tk_tmp_tree, "doc"), ".")
        self._remove_tmp_tree(self.tk_tmp_tree)

#----------------------------------------------------------------------------
    def build(self):
        cmake = self._configure_cmake()
        cmake.configure(source_folder=self._source_subfolder, build_folder = self._build_subfolder)
# Visual Studio sometimes runs "out of heap space"
        if self.settings.compiler == "Visual Studio":
            cmake.parallel = False
        cmake.build()

#----------------------------------------------------------------------------
    def package(self):
        cmake = self._configure_cmake()
        cmake.install(build_dir = self._build_subfolder)

#    def imports(self):
#        self.copy("license*", dst="licenses", folder=True, ignore_case=True)

#----------------------------------------------------------------------------
    def package_info(self):

        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "dbghelp"]
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl", "rt", "m", "pthread", "resolv"]
        elif self.settings.os == "Macos":
            self.cpp_info.system_libs = ["dl", "c", "m", "pthread", "resolv"]
#----------------------------------------------------------------------------
        if self.settings.os == "Windows":
            self.cpp_info.defines.append("_UNICODE")
            self.cpp_info.defines.append("_CRT_SECURE_NO_WARNINGS=1")
        else:
            self.cpp_info.defines.append("_MT")
            self.cpp_info.defines.append("_REENTRANT")
            self.cpp_info.defines.append("_THREAD_SAFE")
            self.cpp_info.defines.append("_LARGEFILE_SOURCE")
            self.cpp_info.defines.append("_LARGEFILE64_SOURCE")
            self.cpp_info.defines.append("_FILE_OFFSET_BITS=64")
        if self.options.shared:
            self.cpp_info.defines.append("NCBI_DLL_BUILD")
        if self.settings.build_type == "Debug":
            self.cpp_info.defines.append("_DEBUG")
        else:
            self.cpp_info.defines.append("NDEBUG")
        self.cpp_info.builddirs.append("res")
        self.cpp_info.build_modules = ["res/build-system/cmake/CMake.NCBIpkg.conan.cmake"]
