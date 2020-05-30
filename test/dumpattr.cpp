#include <storage/Node.h>
#include <stdio.h>
#include <kernel/fs_attr.h>
#include <SupportKit.h>
#include <storage/Mime.h>

int
main(int argc, char **argv)
{
    BNode node = BNode(argv[1]);

    for (;;) {
        char name[B_ATTR_NAME_LENGTH];
        status_t status;
        status = node.GetNextAttrName(name);
        if (status == B_ENTRY_NOT_FOUND)
            break;
        else if (status != B_NO_ERROR) {
            perror(argv[1]);
            return 1;
        }
        attr_info info;
        node.GetAttrInfo(name, &info);
        char val[128], tstr[5];
        int size, i;
        switch (info.type) {
        case B_STRING_TYPE:
        case B_MIME_STRING_TYPE:
            if (info.size < sizeof(val))
                size = info.size;
            else
                size = sizeof(val) - 1;
            node.ReadAttr(name, 0, 0, val, size);
            val[sizeof(val) - 1] = 0;
            break;
	case B_INT32_TYPE:
            int32 xi;
            node.ReadAttr(name, 0, 0, &xi, sizeof(xi));
            sprintf(val, "%d", xi);
            break;
        default:
            char x[8];
            if (info.size < sizeof(x))
                size = info.size;
            else
                size = sizeof(x);
            node.ReadAttr(name, 0, 0, x, size);
            strcpy(val, "0x");
            for (i = 0; i < size; ++i)
                 sprintf(val + i * 2 + 2, "%02x", x[i]);
            if (size < info.size)
                 strcpy(val + i * 2 + 2, "...");
        }
        for (i = 3; i >= 0; --i, info.type >>= 8)
            tstr[i] = info.type & 0xff;
        tstr[4] = 0;
        printf("%s %s %s\n", tstr, name, val);
    }
    return 0;
}
