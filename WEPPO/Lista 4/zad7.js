const readline = require('readline');
const fs = require('fs');
const rl = readline.createInterface({
    input: fs.createReadStream('logs.txt')
});

const ipAddresses = new Map();

rl.on('line', (line) => {
    const ipAddress = line.split(" ")[0];
    //if (ipAddress in ipAddresses) {
    //    ipAddresses[ipAddress] += 1;
    //} else {
    //    ipAddresses[ipAddress] = 1;
    //}
    ipAddresses[ipAddress] = ++ipAddresses[ipAddress] || 1;
})

rl.on('close', () => {
    const auxArray = Object.entries(ipAddresses);
    auxArray.sort(([k1, v1], [k2, v2]) => {
        if (v1 < v2) {
            return 1;
        } else if (v1 > v2) {
            return -1;
        }
        else {
            return 0;
        }
    })

    for (let i = 0; i < 3; i++) {
        console.log(auxArray[i]);
    }
})