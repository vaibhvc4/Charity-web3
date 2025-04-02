// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CharityTracker {
    address public owner;

    struct Charity {
        string name;
        string description;
        string websiteUrl;  // Optional: URL to the charity's website
        string paymentUrl;  // Optional: URL for making payments/donations
        bool verified;
    }

    mapping(address => Charity) public charities;

    event CharityAdded(address indexed donationAddress, string name);
    event CharityVerified(address indexed donationAddress);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Adds a new charity to the tracker.
     * @param _donationAddress The unique address key for the charity.
     * @param _name The charity's name.
     * @param _description A short description of the charity.
     * @param _websiteUrl (Optional) The charity’s website URL.
     * @param _paymentUrl (Optional) A URL for making donations.
     */
    function addCharity(
        address _donationAddress,
        string memory _name,
        string memory _description,
        string memory _websiteUrl,
        string memory _paymentUrl
    ) public {
        require(bytes(_name).length > 0, "Charity name required");
        charities[_donationAddress] = Charity({
            name: _name,
            description: _description,
            websiteUrl: _websiteUrl,
            paymentUrl: _paymentUrl,
            verified: false
        });
        emit CharityAdded(_donationAddress, _name);
    }

    /**
     * @notice Verifies an existing charity. Only the contract owner can call this.
     * @param _donationAddress The charity's donation address to verify.
     */
    function verifyCharity(address _donationAddress) public onlyOwner {
        require(bytes(charities[_donationAddress].name).length > 0, "Charity does not exist");
        charities[_donationAddress].verified = true;
        emit CharityVerified(_donationAddress);
    }

    /**
     * @notice Retrieves the charity details.
     * @param _donationAddress The charity's donation address.
     * @return name The charity's name.
     * @return description The charity's description.
     * @return websiteUrl The charity's website URL (optional).
     * @return paymentUrl The charity's payment URL (optional).
     * @return verified Verification status of the charity.
     */
    function getCharity(address _donationAddress) public view returns (
        string memory name,
        string memory description,
        string memory websiteUrl,
        string memory paymentUrl,
        bool verified
    ) {
        Charity memory charity = charities[_donationAddress];
        return (
            charity.name,
            
            charity.description,
            charity.websiteUrl,
            charity.paymentUrl,
            charity.verified
        );
    }
}
