# Restler:
    please refer to Microsoft git to get more detail information about restler.
    https://github.com/microsoft/restler-fuzzer

# Target
   This git just only is focus of the translation from F# to python for compiler, which is one 
   part of restler. Compiler plays an important role of restler. Its functionalities are to
   transform the swagger/Open API into the restler's grammar. During the procedure,  it analyzes
   the dependencies between the APIs in the file, and compile the annotation, dictionary and example
   into the grammar files if provided with these three files: annotation, dictionary and example.
   
   If you want like to know more works about the compiler, it is the best way to read the source 
   code. By now it is only supported for Swagger2.0.
   
# Usage
   Just for spec only, 
   python .\workflow.py --api_spec ..\..\utest\compiler_ut\swagger\array_example.json
   
   if using the config json file to do some configuration, for example, example, dictionary or annotation etc. you can 
   use the command:
   python .\workflow.py --config ..\..\utest\compiler_ut\swagger\config.json
   
# Summary
  Even though python-compiler is tried to be the same as F#. but there is still more gaps between these two modules.
  Step 1: Make full functionality to python language based on the F# source code. and this task has been finished
  already. 
  Step 2: Pass all test cases are listed in CompilerTest directory. This tasks are ongoing by now. There are still 10 issues
  to be fixed. 
  Step 3: Make more accepted test based on the swagger files with different configuration information to the same output 
  based on the output from these two modules. BTW, the microsoft docker are setup and this is an expected result as reference.
  This task still don't start. will update the status later.
  Step 4: by now, the swagger 2.0 are parsed by the pyswagger with its source code directly. In the near future, it will
  replace by the new parser.
  Step 5: Support the Swagger 3.0 or Open API in the future. 
  
# End
  Thanks Microsoft's restler. If you are interested in this field. you can contact me directly. If you have more requirement 
  of this module, please let me know. 