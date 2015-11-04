from conans import ConanFile
from conans import tools
import platform, os


class BoostConan(ConanFile):
    # Ubuntu: sudo apt-get install g++-4.8-multilib
    # Debian: sudo apt-get install libbz2-dev
    # Debian: sudo apt-get install gcc-4.9-multilib g++-4.9-multilib
    # Debian (for x86 packages):
    #    sudo dpkg --add-architecture i386
    #    sudo apt-get update
    #    sudo apt-get install libbz2-dev:i386
    #
    name = "Boost"
    version = "1.59.0" 
    
    settings = "os", "arch", "compiler", "build_type"   
    FOLDER_NAME = "boost_%s" % version.replace(".", "_")
    ZIP_NAME = "%s.tar.gz" % FOLDER_NAME 
    options = {"shared": [True, False], "header_only": [True, False]}
    default_options = "shared=True", "header_only=False"

    def config(self):
        # If header only, the compiler, etc, does not affect the package!
        # RECURRENT PROBLEM!! premature evaluation
#         if self.options.header_only:
#             self.settings.clear()
#             self.options.remove("shared")
        pass

    def source(self):
        url = "http://sourceforge.net/projects/boost/files/boost/%s/%s/download" % (self.version, self.ZIP_NAME)
        tools.download(url, self.ZIP_NAME)
        tools.unzip(self.ZIP_NAME, ".")
        os.unlink(self.ZIP_NAME)

    def build(self):
        if self.options.header_only:
            return

        command = "bootstrap" if platform.system() == "Windows" else "./bootstrap.sh"
        self.run("cd %s && %s" % (self.FOLDER_NAME, command))

        flags = []
        if self.settings.compiler == "Visual Studio":
            flags.append("toolset=msvc-12.0")

        flags.append("link=%s" % ("static" if not self.options.shared else "shared"))
        if self.settings.compiler == "Visual Studio" and self.settings.compiler.runtime:
            flags.append("runtime-link=%s" % ("static" if "MT" in self.settings.compiler.runtime else "shared"))
        flags.append("variant=%s" % str(self.settings.build_type).lower())
        flags.append("address-model=%s" % ("32" if self.settings.arch == "x86" else "64"))
        b2_flags = " ".join(flags)

        command = "b2" if self.settings.os == "Windows" else "./b2"
        self.run("cd %s && %s %s -j4 --abbreviate-paths --without-python"
                 % (self.FOLDER_NAME, command, b2_flags))

    def package(self):
        self.copy(pattern="*", dst="include/boost", src="%s/boost" % self.FOLDER_NAME)
        self.copy(pattern="*", dst="lib", src="%s/stage/lib" % self.FOLDER_NAME)

    def package_info(self):
        if not self.options.header_only and self.options.shared:
            self.cpp_info.defines.append("BOOST_DYN_LINK")

        libs = ("atomic chrono container context coroutine date_time exception filesystem "
                "graph iostreams locale log_setup log math_c99 math_c99f math_c99l math_tr1 "
                "math_tr1f math_tr1l prg_exec_monitor program_options random regex serialization "
                "signals system test_exec_monitor thread timer unit_test_framework wave "
                "wserialization").split()
        if self.settings.os != "Windows":
            self.cpp_info.libs.extend(["boost_%s" % lib for lib in libs])
