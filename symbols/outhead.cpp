
// for screen_id, BPoint, pattern
#include <interface/GraphicsDefs.h>
#include <interface/Point.h>
#include <interface/Font.h>
#include <stdio.h>
// for BCursor
#include <app/Cursor.h>

static void
out(const char *name, const unsigned char *val)
{
	const unsigned char *cp;
	printf("%s = \"", name);
	for (cp = val; *cp; ++cp) {
		if (*cp >= 127 || *cp < 32)
			printf("\\x%02x", *cp);
		else
			putchar(*cp);
	}
	puts("\"");
}

static void
out(const char *name, const char *val)
{
	out(name, (const unsigned char *) val);
}

static void
out(const char *name, unsigned long long val)
{
	unsigned long low, high;
	printf("%s = 0x", name);
	low = val & 0xffffffff;
	high = val >> 32;
	if (high)
		printf("%08x", high);
	printf("%08xL\n", low);
}

static void
out(const char *name, long long val)
{
	out(name, (unsigned long long) val);
}

static void
out(const char *name, unsigned long val)
{
	if (val > 65535)
		printf("%s = 0x%08x\n", name, val);
	else if (val > 255)
		printf("%s = 0x%04x\n", name, val);
	else if (val > 16)
		printf("%s = 0x%02x\n", name, val);
	else
		printf("%s = %d\n", name, val);
}

static void
out(const char *name, unsigned int val)
{
	out(name, (unsigned long) val);
}

static void
out(const char *name, long val)
{
	out(name, (unsigned long) val);
}

static void
out(const char *name, int val)
{
	out(name, (unsigned long) val);
}

static void
out(const char *name, double val)
{
	printf("%s = %f\n", name, val);
}

static void
out(const char *name, screen_id val)
{
	printf("%s = (%d,)\n", name, val.id);
}

static void
out(const char *name, BPoint val)
{
	printf("%s = (%d, %d)\n", name, val.x, val.y);
}

static void
out(const char *name, pattern val)
{
}

static void
out(const char *name, const BCursor *val)
{
}

static void
out(const char *name, const rgb_color val)
{
}

static void
out(const char *name, const unicode_block val)
{
}

int
main(int argc, char **argv)
{
