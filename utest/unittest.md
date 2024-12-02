# unit test
  There are two parts - compiler_ut and restler_ut. 
  
## compiler_ut 
  This part comes from CompilerTest from Microsoft Restler. Totally copy the swagger files and test cases from there.
  You can find swagger files under swagger folders. 
  Using the compiler_ut.json swith debug/execute all mode for compiler unit test cases.
  
  Except the unit test cases, the combined test cases will be added in order to make sure that all requirements are met
  the original compiler from Microsoft. This part maybe move to acceptance test. Just wait for a final decision in the future.
  

## restler_ut
  Pick up from restler unit test part. Removed the test cases related to test_server part.