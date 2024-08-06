import configparser

# locals.cfg is used to overwrite init.cfg and omit upload to github repository via .gitignore
candidates = ["init.cfg", "locals.cfg"]

# create parser object and read config file
config = configparser.RawConfigParser()
found = config.read(candidates)

missing = set(candidates) - set(found)

if "locals.cfg" in missing:
    print(
        """Hint: 'locals.cfg' is used to overwrite parameters in 'init.cfg' and 
          omit upload of secret and local parameters to github repository 
          via '.gitignore'.
          Please set missing config parameters in 'init.cfg' and try again.
          """
    )

print("Found config files:", sorted(found))
print("Missing files     :", sorted(missing))
