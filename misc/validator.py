#!/usr/bin/env python
#
# validate and build a student submission
# Must run in Python 2.6 because of Cloudera Quickstart VM

import sys,zipfile,os,os.path
import ConfigParser
optional = []
from subprocess import Popen,PIPE,call

class Validator:

    def __init__(self,cfg_name=None):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(cfg_name)
        self.name = cfg.get("PS","name")
        self.required = cfg.get("PS","required_files").replace(","," ").split()
        self.optional = cfg.get("PS","optional_files").replace(","," ").split()

    def fname(self):
        return self.name+".zip"

    def ignore_file(self,fname):
        if len(fname)==0: return True
        if fname[0] in "._": return True
        base = os.path.basename(fname)
        if base[0] in "._": return True
        return False

    def build_zip(self,fname):
        required_missing = 0
        print("Building {0}".format(fname))
        z = zipfile.ZipFile(fname,"w",zipfile.ZIP_DEFLATED)
        for fn in self.required + self.optional:
            if os.path.exists(fn):
                print("Adding {0}...".format(fn))
                z.write(fn)
            else:
                if fn in required:
                    msg = "REQUIRED FILE "
                    required_missing += 1
                else:
                    msg = ""
                print("{0} Not found {1}...".format(msg, fn))

        z.close()
        print("Done!\n\n")
        call(['ls','-l',fname])
        print("\n")
        call(['unzip','-l',fname])
        if required_missing > 0:
            print("\n*** REQUIRED FILES MISSING: {0} ***".format(required_missing))
        exit(0)

    def validate_file(self,z,fname,fbase,hook):
        import py_compile
        errors = 0
        # Get the file contents
        contents = z.open(fname).read()

        # Unpack if the file is python or if we have a hook
        # If python file, see if it compiles
        if fbase.endswith(".py") or hook:
            fnew = "unpack/"+fbase
            with open(fnew,"w") as fb:
                fb.write(contents)

        # Verify python correctness if it is a python file
        if fbase.endswith(".py"):
            try:
                py_compile.compile(fnew)
            except py_compile.PyCompileError as e:
                print("Compile error: "+str(e))
                errors += 1

        # If this is a text file, complain if it is RTF
        if fname.endswith(".txt") and contents.startswith(r"{\rtf"):
            print("*** {0} is a RTF file; it should be a text file".format(fname))
            errors += 1

        if hook:
            hook(fbase,fnew)
        return errors


    def validate(self,zfile,hook=None):
        try:
            os.mkdir("unpack")
        except OSError as e:
            pass
        found_required = set()
        found_optional = set()
        found_unwanted = set()
        errors = 0
        print("Validating {0} ...\n".format(zfile))
        z = zipfile.ZipFile(zfile)
        for f in z.filelist:
            fname = f.orig_filename
            if ignore_file(fname): continue
            fbase = os.path.basename(fname)
            if fbase in required:
                found_required.add(fbase)
                errors += validate_file(z,fname,fbase,hook)
                continue
            if fbase in optional:
                found_optional.add(fbase)
                errors += validate_file(z,fname,fbase,hook)
                continue
            found_unwanted.add(fbase)

        def print_file_list(title,files):
            if files:
                print(title)
                for word in files:
                    print("\t"+word)

        print("")
        print_file_list("Found required files:",found_required)
        print_file_list("Found optional files:",found_optional)

        print_file_list("MISSING REQUIRED FILES:",required.symmetric_difference(found_required)) 
        print_file_list("MISSING OPTIONAL FILES:",optional.symmetric_difference(found_optional)) 
        if errors:
            print("TOTAL ERRORS: {0}".format(errors))
        return(errors)

if __name__=="__main__":
    # Read the config file

    v = Validator("validator.cfg")

    if len(sys.argv)>1:
        if sys.argv[1]=="--zip":
            v.build_zip(v.fname())
    fname = v.fname()
    print("v.fname:{}".format(fname))
    code = v.validate(fname)
    exit(code)

