async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contract with account:", deployer.address);
  
    const CharityTracker = await ethers.getContractFactory("CharityTracker");
    const charityTracker = await CharityTracker.deploy();
    await charityTracker.deployed();
  
    console.log("CharityTracker deployed to:", charityTracker.address);
  }
  
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
  