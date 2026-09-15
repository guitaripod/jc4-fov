#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

typedef long long (__stdcall *OodleDec)(const void*, long long, void*, long long,
    int, int, int, void*, long long, void*, long long, void*, long long, int);

int main(int argc, char** argv) {
    if (argc < 2) { fprintf(stderr, "usage: oodle_dec jobs.txt\n"); return 2; }
    HMODULE h = LoadLibraryA("oo2core_7_win64.dll");
    if (!h) { fprintf(stderr, "LoadLibrary failed %lu\n", GetLastError()); return 3; }
    OodleDec dec = (OodleDec)GetProcAddress(h, "OodleLZ_Decompress");
    if (!dec) { fprintf(stderr, "GetProcAddress failed\n"); return 4; }

    FILE* jobs = fopen(argv[1], "r");
    if (!jobs) { fprintf(stderr, "open jobs failed\n"); return 5; }
    char line[4096];
    int ok = 0, fail = 0;
    while (fgets(line, sizeof(line), jobs)) {
        char arc[1024], out[1024];
        long long off, csize, usize;
        if (sscanf(line, "%1023[^\t]\t%lld\t%lld\t%lld\t%1023[^\t\r\n]", arc, &off, &csize, &usize, out) != 5) continue;
        FILE* fi = fopen(arc, "rb");
        if (!fi) { fprintf(stderr, "ERR open %s\n", arc); fail++; continue; }
        unsigned char* cb = (unsigned char*)malloc((size_t)csize);
        unsigned char* ub = (unsigned char*)malloc((size_t)usize + 64);
        _fseeki64(fi, off, SEEK_SET);
        if (fread(cb, 1, (size_t)csize, fi) != (size_t)csize) { fprintf(stderr, "ERR read %s\n", arc); fail++; goto next; }
        {
            long long r = dec(cb, csize, ub, usize, 1, 0, 0, NULL, 0, NULL, 0, NULL, 0, 3);
            if (r != usize) { fprintf(stderr, "ERR decode %s -> %lld != %lld\n", out, r, usize); fail++; goto next; }
        }
        {
            FILE* fo = fopen(out, "wb");
            if (!fo) { fprintf(stderr, "ERR create %s\n", out); fail++; goto next; }
            fwrite(ub, 1, (size_t)usize, fo);
            fclose(fo);
            ok++;
        }
    next:
        free(cb); free(ub); fclose(fi);
    }
    fclose(jobs);
    fprintf(stderr, "done ok=%d fail=%d\n", ok, fail);
    return fail ? 1 : 0;
}
