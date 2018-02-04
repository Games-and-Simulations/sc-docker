You should put your version of JRE here.

You can put it under `jre_8_32bit_noinstall.zip`

The way I've done it is to just zip
windows 32bit oracle java 8 folder and it works.

You'll need to change a line in ./dockerfiles/java.dockerfile
where it says

`&&mv jre1.8.0_<some version>`

change that to

`&&mv <name of your windows 32bit oracle java 8 folder>`


The zip file isn't included in the repo because of potential license problems.
