
// Local testing code to compare against Python implementation. Requires Node 14+ to run.
const promisify = require('util').promisify;
const exec = promisify(require('child_process').exec);
const fs = require('fs/promises');
const {
    readCodewords, decompressLZW, decompressRLE, decompress,
    compressRLE, compressLZW, packCodewords, compress,
} = require('./u6-lzw.js');

const KNOWN_FILE_OFFSETS = [
    0x01d700, 0x028060, 0x029e50, 0x02ddb0, 0x02e590, 0x02f1d0, 0x02f920, 0x048000,
    0x049d00, 0x04b900, 0x04df00, 0x050000, 0x051b00, 0x053900, 0x055f80, 0x058000,
    0x05ba80, 0x05d480, 0x060000, 0x061a00, 0x062e00, 0x065e00, 0x067180, 0x068000,
    0x069e80, 0x06bb80, 0x06d480, 0x070000, 0x071600, 0x073680, 0x075080, 0x075a80,
    0x076200, 0x076980, 0x077100, 0x096b00, 0x09d000, 0x09da00, 0x09e300, 0x09ec00,
    0x09f500, 0x0bf100, 0x0cd400, 0x0cea80, 0x0d0000, 0x0d2180, 0x0d4200, 0x0d6600,
    0x0d6800, 0x0d6d80, 0x0d7000, 0x0d7280, 0x0d7500, 0x0d8000, 0x0d9500, 0x0da300,
    0x0dc100, 0x0de100, 0x0df200, 0x0e0000, 0x0e1000, 0x0e3200,
];

function assertArraysSame(prefixMsg, expected, actual) {
    var errors = 0;
    if (expected.length !== actual.length) {
        console.error(`${prefixMsg}: expected length ${expected.length} actual length ${actual.length}`)
        errors++
    }
    for (var i = 0; i < Math.max(expected.length, actual.length); i++) {
        if (expected[i] !== actual[i]) {
            errors++;
            console.error(`${prefixMsg}: byte ${i} expected ${expected[i]} found ${actual[i]}`);
            if (errors > 4) {
                return false
            }
        }
    }
    return true
}

async function testDecompression(fileOffsets) {
    const rom = new Uint8Array(await fs.readFile('./u6.sfc'));

    for (let offset of fileOffsets) {
        const offsetStr = `0x${offset.toString(16)}`;
        const filename = `./files/${offsetStr}.raw`;
        try {
            // Check if file was already decompressed by the Python implementation
            await fs.stat(filename);
        } catch {
            // If not, decompress it
            await fs.mkdir('./files/', {recursive: true});
            await exec(`./decompress.py u6.sfc:${offsetStr} ${filename}`);
        }
        const expectedContent = await fs.readFile(filename);
        console.log(`Checking ${offsetStr}`);
        const actualContent = decompress(rom, offset);

        assertArraysSame(offsetStr, expectedContent, actualContent);
    }
}

async function testCompression(fileOffsets) {
    const rom = new Uint8Array(await fs.readFile('./u6.sfc'));

    for (let offset of fileOffsets) {
        const offsetStr = `0x${offset.toString(16)}`;
        console.log(`Checking ${offsetStr}`);
        // Assert that decompressed content is the same as decompressed-recompressed-decompressed content.
        const {codewords: inputCodewords, bytesRead: inputBytes} = readCodewords(rom, offset);
        const content = decompressRLE(decompressLZW(inputCodewords));

        const compRLE = compressRLE(content);
        const compCodewords = compressLZW(compRLE);
        const recompressed = packCodewords(compCodewords);
        const {codewords, bytesRead} = readCodewords(recompressed, 0);
        const decompRLE = decompressLZW(codewords);
        const decompressed = decompressRLE(decompRLE);
        console.log(inputBytes, content.length, recompressed.length, bytesRead, decompressed.length);

        try {
            assertArraysSame(`${offsetStr} CWs`, compCodewords, codewords);
        } catch (ex) {
            console.error(ex.message)
        }

        try {
            assertArraysSame(`${offsetStr} RLE`, compRLE, decompRLE);
        } catch (ex) {
            console.error(ex.message)
        }

        try {
            assertArraysSame(offsetStr, content, decompressed);
        } catch (ex) {
            console.error(ex.message)
        }
    }
}

async function testCompressionVsPython(fileOffsets) {
    const rom = new Uint8Array(await fs.readFile('./u6.sfc'));

    for (let offset of fileOffsets) {
        const offsetStr = `0x${offset.toString(16)}`;
        const decompFilename = `./files/${offsetStr}.raw`;
        const recompFilename = `./files/${offsetStr}_recomp.raw`;
        const compressedLength = readCodewords(rom, offset).bytesRead;
        const romContent = rom.subarray(offset, offset + compressedLength);
        console.log(`Checking ${offsetStr} vs ROM`);
        const recompressedContent = compress(decompress(rom, offset));
        if (assertArraysSame(offsetStr, romContent, recompressedContent)) {
            continue;
        }
        console.log(`Checking ${offsetStr} vs Python`);

        try {
            // Check if file was already decompressed by the Python implementation
            await fs.stat(filename);
        } catch {
            // If not, decompress it
            await fs.mkdir('./files/', {recursive: true});
            await exec(`./decompress.py u6.sfc:${offsetStr} ${decompFilename}`);
        }
        try {
            // Check if file was already recompressed by the Python implementation
            await fs.stat(filename);
        } catch {
            // If not, recompress it
            await exec(`./compress.py ${decompFilename} ${recompFilename}`);
        }
        const expectedContent = await fs.readFile(recompFilename);


        assertArraysSame(offsetStr, expectedContent, recompressedContent);
    }
}

async function writeDebugFiles(offset) {
    const rom = new Uint8Array(await fs.readFile('./u6.sfc'));
    const offsetStr = `0x${offset.toString(16)}`;
    await fs.mkdir('./debug/', {recursive: true});

    const {codewords, bytesRead} = readCodewords(rom, offset);
    await fs.writeFile(`./debug/${offsetStr}_decomp_cw.txt`, codewords.map(c=>c.toString(16)).join('\n'));
    await fs.writeFile(`./debug/${offsetStr}_input.raw`, rom.subarray(offset, offset + bytesRead));

    const decompRLE = decompressLZW(codewords);
    await fs.writeFile(`./debug/${offsetStr}_decomp_rle.raw`, decompRLE);
    const decompressed = decompressRLE(decompRLE);
    await fs.writeFile(`./debug/${offsetStr}_decompressed.raw`, decompressed);

    const compRLE = compressRLE(decompressed);
    await fs.writeFile(`./debug/${offsetStr}_recomp_rle.raw`, compRLE);
    const compCodewords = compressLZW(compRLE);
    await fs.writeFile(`./debug/${offsetStr}_recomp_cw.txt`, compCodewords.map(c=>c.toString(16)).join('\n'));
    const recompressed = packCodewords(compCodewords);
    await fs.writeFile(`./debug/${offsetStr}_recompressed.raw`, recompressed);

}

async function runAllTests() {
    // await writeDebugFiles(0x29e50);
    console.log('Testing decompression');
    await testDecompression(KNOWN_FILE_OFFSETS);

    console.log('Testing compression against ROM and Python implementation');
    await testCompressionVsPython(KNOWN_FILE_OFFSETS);
    console.log('Testing compression + decompression');
    await testCompression(KNOWN_FILE_OFFSETS);
}
