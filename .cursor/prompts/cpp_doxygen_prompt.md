# NOTES
This requires that you first run build_docs.sh, stop it once the repo.log is populated with warnings and then run python3 tools/isaac/parse_doxygen_warnings.py to generate the doxygen_warnings.txt file. The idea is that you guide the LLM through the files that need to be updated rather than trying to get it to do it all at once. I have found that this works much better and the LLM doesn't get overwhelmed.

# Copy this prompt into the chat and run it.
add all missing documentation listed in @doxygen_warnings.txt one file at a time, Using the rules from @cpp_doxygen_rules.mdc. Ensuring that absolutely no code is modified, refactored, added or removed in any way. Be thorough and do not skip any files, or functions. Fully document a file before moving on to the next one.





