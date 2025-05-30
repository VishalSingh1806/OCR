import React from 'react'
import logo from '../assets/images/logo.png';

const Navbar = () => {
  return (
    <div className=' sticky top-0 z-20 bg-primary text-white p-6'>
        <img className='w-[145px]' src={logo} alt='Recircle Logo'/>
    </div>
  )
}

export default Navbar